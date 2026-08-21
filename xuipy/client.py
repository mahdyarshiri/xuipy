import threading
import time
import requests

from typing import Any, Dict, List, Optional, Union
from xuipy.exceptions import XUIAuthError, XUIRequestError, XUIValidationError

# Every panel endpoint ultimately resolves to one of these shapes.
XUIResponse = Union[Dict[str, Any], List[Any], str, bool]


class XUI:
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, api_token: Optional[str] = None,timeout: int = 10,):
        if not base_url:
            raise XUIValidationError("base_url must not be empty")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._csrf_token: Optional[str] = None
        self._csrf_lock = threading.Lock()
        self._auth_lock = threading.Lock()

        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})
        elif username and password:
            self.username = username
            self.password = password
            self._login()
        else:
            raise XUIValidationError("Provide either (username and password) or api_token")

    def __enter__(self) -> "XUI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    # =============== REQUEST HANDLING ===============
    def _request(self, method: str, path: str, json_data: Optional[dict] = None, params: Optional[dict] = None, error_msg: str = "Request failed", _retry_auth: bool = True, _retry_csrf: bool = True,) -> XUIResponse:
        headers = {}
        using_bearer = "Authorization" in self.session.headers
        if method.upper() != "GET" and not using_bearer:
            headers["X-CSRF-Token"] = self._get_csrf_token()
        try:
            response = self.session.request(method, f"{self.base_url}{path}", json=json_data, params=params, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise XUIRequestError(f"{error_msg}: {e}") from e

        # If a cached CSRF token was stale, refresh it once and retry
        if response.status_code == 403 and not using_bearer and method.upper() != "GET" and _retry_csrf:
            headers["X-CSRF-Token"] = self._get_csrf_token(force_refresh=True)
            try:
                response = self.session.request(method, f"{self.base_url}{path}", json=json_data, params=params, headers=headers, timeout=self.timeout)
            except requests.RequestException as e:
                raise XUIRequestError(f"{error_msg}: {e}") from e

        # If the session cookie itself expired (not just the CSRF token), and we were
        # authenticated via username/password, transparently re-login once and retry
        # the original request. Bearer-token auth and the /login call itself never
        # attempt this, to avoid recursing on genuinely bad credentials.
        if response.status_code in (401, 403):
            if not using_bearer and _retry_auth and hasattr(self, "username"):
                with self._auth_lock:
                    self._login()
                return self._request(method, path, json_data=json_data, params=params, error_msg=error_msg, _retry_auth=False, _retry_csrf=_retry_csrf,)
            raise XUIAuthError(f"{error_msg}: authentication failed (HTTP {response.status_code})")

        # Try to parse the panel's JSON body first so a 4xx/5xx with a useful
        # "msg" field isn't swallowed by raise_for_status() before we can read it.
        try:
            data = response.json()
        except ValueError as e:
            try:
                response.raise_for_status()
            except requests.RequestException as http_err:
                raise XUIRequestError(f"{error_msg}: {http_err}") from http_err
            raise XUIRequestError(f"{error_msg}: {e}") from e

        if not data.get("success"):
            raise XUIRequestError(f"{error_msg}: {data.get('msg', 'unknown error')}")

        if data.get("obj") is not None:
            return data.get("obj")
        return data.get("msg") or True

    # =============== AUTHENTICATION ===============
    def _get_csrf_token(self, force_refresh: bool = False) -> str:
        """Return the cached CSRF token, fetching a fresh one if not cached or force_refresh=True."""
        if self._csrf_token is not None and not force_refresh:
            return self._csrf_token

        with self._csrf_lock:
            if self._csrf_token is not None and not force_refresh:
                return self._csrf_token

            try:
                response = self.session.get(f"{self.base_url}/csrf-token", timeout=self.timeout)
            except requests.RequestException as e:
                raise XUIRequestError(f"Failed to get CSRF token: {e}") from e
            if response.status_code in (401, 403):
                raise XUIAuthError(f"Failed to get CSRF token: authentication failed (HTTP {response.status_code})")
            try:
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                raise XUIRequestError(f"Failed to get CSRF token: {e}") from e

            if not data.get("success"):
                raise XUIAuthError(f"Failed to get CSRF token: {data.get('msg', 'unknown error')}")

            self._csrf_token = data["obj"]
            return self._csrf_token

    def _login(self) -> XUIResponse:
        """Authenticate with username + password and receive a session cookie."""
        return self._request("POST", "/login", json_data={"username": self.username, "password": self.password}, error_msg="Login failed",_retry_auth=False,)

    def logout(self) -> XUIResponse:
        """Clear the session cookie."""
        return self._request("POST", "/logout", error_msg="Logout failed")

    def get_two_factor_enable(self) -> XUIResponse:
        """Return whether 2FA is enabled on the panel."""
        return self._request("POST", "/getTwoFactorEnable", error_msg="Failed to check 2FA status")

    # =============== INBOUNDS ===============
    def get_inbounds(self) -> XUIResponse:
        """List every inbound owned by the authenticated user, including clientStats traffic counters."""
        return self._request("GET", "/panel/api/inbounds/list", error_msg="Failed to get inbounds")

    def get_inbounds_slim(self) -> XUIResponse:
        """Same as get_inbounds but with client details stripped down. Use for list pages."""
        return self._request("GET", "/panel/api/inbounds/list/slim", error_msg="Failed to get slim inbounds")

    def get_inbound_options(self) -> XUIResponse:
        """Lightweight picker projection (id, remark, tag, protocol, port). Use for dropdowns."""
        return self._request("GET", "/panel/api/inbounds/options", error_msg="Failed to get inbound options")

    def get_all_links(self) -> XUIResponse:
        """Return every protocol URL (vless://, vmess://, etc.) across all inbounds and clients."""
        return self._request("GET", "/panel/api/inbounds/allLinks", error_msg="Failed to get all links")

    def get_inbound(self, inbound_id: int) -> XUIResponse:
        """Fetch a single inbound by numeric ID."""
        return self._request("GET", f"/panel/api/inbounds/get/{inbound_id}", error_msg=f"Failed to get inbound {inbound_id}")

    def add_inbound(self, inbound_data: dict) -> XUIResponse:
        """Create a new inbound. inbound_data must include protocol, port, settings, streamSettings, sniffing, remark."""
        if not inbound_data.get("remark"):
            raise XUIValidationError("inbound_data must include a non-empty 'remark'")
        if not inbound_data.get("port"):
            raise XUIValidationError("inbound_data must include a 'port'")

        return self._request("POST", "/panel/api/inbounds/add", json_data=inbound_data, error_msg="Failed to add inbound")

    def update_inbound(self, inbound_id: int, inbound_data: dict) -> XUIResponse:
        """Replace an inbound's configuration. Body shape mirrors add_inbound."""
        if not inbound_data.get("remark"):
            raise XUIValidationError("inbound_data must include a non-empty 'remark'")
        if not inbound_data.get("port"):
            raise XUIValidationError("inbound_data must include a 'port'")

        return self._request("POST", f"/panel/api/inbounds/update/{inbound_id}", json_data=inbound_data, error_msg=f"Failed to update inbound {inbound_id}")

    def delete_inbound(self, inbound_id: int) -> XUIResponse:
        """Delete an inbound by ID. Also removes its associated client stats rows."""
        return self._request("POST", f"/panel/api/inbounds/del/{inbound_id}", error_msg=f"Failed to delete inbound {inbound_id}")

    def bulk_delete_inbounds(self, inbound_ids: List[int]) -> XUIResponse:
        """Delete many inbounds in one call. Failures are reported per id."""
        if not inbound_ids:
            raise XUIValidationError("inbound_ids must not be empty")
        return self._request("POST", "/panel/api/inbounds/bulkDel", json_data={"ids": inbound_ids}, error_msg="Failed to bulk delete inbounds")

    def set_inbound_enable(self, inbound_id: int, enable: bool) -> XUIResponse:
        """Toggle only the enable flag without re-serialising the whole settings JSON."""
        return self._request("POST", f"/panel/api/inbounds/setEnable/{inbound_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on inbound {inbound_id}")

    def reset_inbound_traffic(self, inbound_id: int) -> XUIResponse:
        """Zero out upload + download counters for a single inbound."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/resetTraffic", error_msg=f"Failed to reset traffic for inbound {inbound_id}")

    def reset_all_traffics(self) -> XUIResponse:
        """Reset upload + download counters on every inbound. Destructive."""
        return self._request("POST", "/panel/api/inbounds/resetAllTraffics", error_msg="Failed to reset all traffics")

    def delete_all_clients(self, inbound_id: int) -> XUIResponse:
        """Remove every client attached to a single inbound while keeping the inbound itself. Destructive."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/delAllClients", error_msg=f"Failed to delete all clients on inbound {inbound_id}")

    def get_fallbacks(self, inbound_id: int) -> XUIResponse:
        """List the fallback rules attached to a master VLESS/Trojan TCP-TLS inbound."""
        return self._request("GET", f"/panel/api/inbounds/{inbound_id}/fallbacks", error_msg=f"Failed to get fallbacks for inbound {inbound_id}")

    def set_fallbacks(self, inbound_id: int, fallbacks: list) -> XUIResponse:
        """Replace the entire fallback list for a master inbound. Triggers an Xray restart."""
        return self._request(
            "POST", f"/panel/api/inbounds/{inbound_id}/fallbacks", json_data={"fallbacks": fallbacks}, error_msg=f"Failed to set fallbacks for inbound {inbound_id}")

    # =============== CLIENTS ===============
    def get_clients(self) -> XUIResponse:
        """List every client with its attached inbound IDs and traffic record."""
        return self._request("GET", "/panel/api/clients/list", error_msg="Failed to get clients")

    def get_clients_paged(self, **params) -> XUIResponse:
        """Filter, sort, and paginate clients on the server. Pass query params like page, size, search."""
        return self._request("GET", "/panel/api/clients/list/paged", params=params, error_msg="Failed to get paged clients")

    def get_client(self, email: str) -> XUIResponse:
        """Fetch one client by email, including its attached inbound IDs."""
        return self._request("GET", f"/panel/api/clients/get/{email}", error_msg=f"Failed to get client {email}")

    @staticmethod
    def _expiry_ms(expiry_days: int) -> int:
        """Convert a relative day count into an absolute epoch-ms expiry, or 0 for 'never expires'."""
        if expiry_days == 0:
            return 0
        return int(time.time() * 1000) + (expiry_days * 1000 * 60 * 60 * 24)

    def add_client(self, email: str, inbound_ids: Optional[List[int]] = None, enable: bool = True, expiry_days: int = 0, total_gb: float = 0, tg_id: int = 0,) -> XUIResponse:
        """Create a new client and attach it to one or more inbounds. Secrets (uuid/password) auto-generated by the panel."""
        if not email:
            raise XUIValidationError("email must not be empty")

        if inbound_ids is None:
            inbound_ids = [i["id"] for i in self.get_inbound_options()]

        client_data = {
            "email": email,
            "enable": enable,
            "expiryTime": self._expiry_ms(expiry_days),
            "totalGB": int(total_gb * 1024 * 1024 * 1024),
            "tgId": tg_id,
        }
        return self._request("POST", "/panel/api/clients/add", json_data={"client": client_data, "inboundIds": inbound_ids}, error_msg="Failed to add client")

    def update_client(self, email: str, enable: bool = True, expiry_days: int = 0, total_gb: float = 0, tg_id: int = 0,) -> XUIResponse:
        """Update an existing client by email. Replaces the full row — pass all fields you want kept."""
        if not email:
            raise XUIValidationError("email must not be empty")

        data = {
            "email": email,
            "enable": enable,
            "expiryTime": self._expiry_ms(expiry_days),
            "totalGB": int(total_gb * 1024 * 1024 * 1024),
            "tgId": tg_id,
        }
        return self._request("POST", f"/panel/api/clients/update/{email}", json_data=data, error_msg=f"Failed to update client {email}")

    def delete_client(self, email: str, keep_traffic: bool = False) -> XUIResponse:
        """Delete a client by email. Set keep_traffic=True to retain its traffic record."""
        if not email:
            raise XUIValidationError("email must not be empty")
        params = {"keepTraffic": 1} if keep_traffic else {}
        return self._request("POST", f"/panel/api/clients/del/{email}", params=params, error_msg=f"Failed to delete client {email}")

    def reset_client_traffic(self, email: str) -> XUIResponse:
        """Zero out a single client's up/down counters and re-enable it if it was depleted."""
        return self._request("POST", f"/panel/api/clients/resetTraffic/{email}", error_msg=f"Failed to reset traffic for client {email}")

    def get_client_ips(self, email: str) -> XUIResponse:
        """List source IPs that have connected with this client's credentials."""
        return self._request("POST", f"/panel/api/clients/ips/{email}", error_msg=f"Failed to get IPs for client {email}")

    def get_client_traffic(self, email: str) -> XUIResponse:
        """Traffic counters for a client identified by email."""
        return self._request("GET", f"/panel/api/clients/traffic/{email}", error_msg=f"Failed to get traffic for client {email}")

    def get_client_links(self, email: str) -> XUIResponse:
        """Return every share URL for one client across all attached inbounds."""
        return self._request("GET", f"/panel/api/clients/links/{email}", error_msg=f"Failed to get links for client {email}")

    # =============== NODES ===============
    def get_nodes(self) -> XUIResponse:
        """List every configured node with its connection details, health, and last heartbeat."""
        return self._request("GET", "/panel/api/nodes/list", error_msg="Failed to get nodes")

    def get_node(self, node_id: int) -> XUIResponse:
        """Fetch a single node by ID."""
        return self._request("GET", f"/panel/api/nodes/get/{node_id}", error_msg=f"Failed to get node {node_id}")

    def add_node(self, url: str, api_token: str, remark: str = "", allow_private_address: bool = False) -> XUIResponse:
        """Register a new remote node."""
        if not url:
            raise XUIValidationError("url must not be empty")
        if not api_token:
            raise XUIValidationError("api_token must not be empty")
        data = {
            "url": url,
            "apiToken": api_token,
            "remark": remark,
            "allowPrivateAddress": allow_private_address,
        }
        return self._request("POST", "/panel/api/nodes/add", json_data=data, error_msg="Failed to add node")

    def update_node(self, node_id: int, node_data: dict) -> XUIResponse:
        """Replace a node's connection details. Omit apiToken to keep the stored token, or set clearApiToken=True to clear it."""
        if not node_data:
            raise XUIValidationError("node_data must not be empty")
        return self._request("POST", f"/panel/api/nodes/update/{node_id}", json_data=node_data, error_msg=f"Failed to update node {node_id}")

    def delete_node(self, node_id: int) -> XUIResponse:
        """Delete a node. Inbounds bound to it are not auto-migrated."""
        return self._request("POST", f"/panel/api/nodes/del/{node_id}", error_msg=f"Failed to delete node {node_id}")

    def set_node_enable(self, node_id: int, enable: bool) -> XUIResponse:
        """Pause or resume traffic sync with this node."""
        return self._request("POST", f"/panel/api/nodes/setEnable/{node_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on node {node_id}")

    def probe_node(self, node_id: int) -> XUIResponse:
        """Probe an existing node, updating its cached health state."""
        return self._request("POST", f"/panel/api/nodes/probe/{node_id}", error_msg=f"Failed to probe node {node_id}")

    # =============== HOSTS ===============
    def get_hosts(self) -> XUIResponse:
        """List every host across all inbounds, grouped by inbound then ordered by sort order."""
        return self._request("GET", "/panel/api/hosts/list", error_msg="Failed to get hosts")

    def get_host(self, group_id: str) -> XUIResponse:
        """Fetch a single host group by Group ID."""
        return self._request("GET", f"/panel/api/hosts/get/{group_id}", error_msg=f"Failed to get host {group_id}")

    def get_hosts_by_inbound(self, inbound_id: int) -> XUIResponse:
        """Fetch one inbound's hosts, grouped by host group."""
        return self._request("GET", f"/panel/api/hosts/byInbound/{inbound_id}", error_msg=f"Failed to get hosts for inbound {inbound_id}")

    def get_host_tags(self) -> XUIResponse:
        """Distinct, sorted set of tags used across all hosts."""
        return self._request("GET", "/panel/api/hosts/tags", error_msg="Failed to get host tags")

    def add_host(self, host_data: dict) -> XUIResponse:
        """Create a host group on inbounds."""
        if not host_data:
            raise XUIValidationError("host_data must not be empty")
        return self._request("POST", "/panel/api/hosts/add", json_data=host_data, error_msg="Failed to add host")

    def update_host(self, group_id: str, host_data: dict) -> XUIResponse:
        """Replace a host group's content."""
        if not group_id:
            raise XUIValidationError("group_id must not be empty")
        if not host_data:
            raise XUIValidationError("host_data must not be empty")
        return self._request("POST", f"/panel/api/hosts/update/{group_id}", json_data=host_data, error_msg=f"Failed to update host {group_id}")

    def delete_host(self, group_id: str) -> XUIResponse:
        """Delete a host group."""
        return self._request("POST", f"/panel/api/hosts/del/{group_id}", error_msg=f"Failed to delete host {group_id}")

    def set_host_enable(self, group_id: str, enable: bool) -> XUIResponse:
        """Enable or disable a host group."""
        return self._request("POST", f"/panel/api/hosts/setEnable/{group_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on host {group_id}")

    def reorder_hosts(self, group_ids: list) -> XUIResponse:
        """Set host group sort order by the position of each groupId in the array."""
        if not group_ids:
            raise XUIValidationError("group_ids must not be empty")
        return self._request("POST", "/panel/api/hosts/reorder", json_data={"groupIds": group_ids}, error_msg="Failed to reorder hosts")

    # =============== SERVER ===============
    def get_server_status(self) -> XUIResponse:
        """Real-time machine snapshot: CPU, memory, swap, disk, network IO, load averages, Xray state."""
        return self._request("GET", "/panel/api/server/status", error_msg="Failed to get server status")

    def get_fail2ban_status(self) -> XUIResponse:
        """Reports whether per-client IP limits can be enforced on this host."""
        return self._request("GET", "/panel/api/server/fail2banStatus", error_msg="Failed to get fail2ban status")

    def get_server_history(self, metric: str, bucket: str) -> XUIResponse:
        """Aggregated time-series for one metric over the last ~6 hours. bucket: interval size in seconds as a string, e.g. "60" for 1-minute buckets."""
        return self._request("GET", f"/panel/api/server/history/{metric}/{bucket}", error_msg=f"Failed to get history for {metric}")

    def get_xray_metrics_state(self) -> XUIResponse:
        """Xray runtime metrics state: whether metrics are configured and current snapshot values."""
        return self._request("GET", "/panel/api/server/xrayMetricsState", error_msg="Failed to get xray metrics state")

    def get_xray_version(self) -> XUIResponse:
        """List Xray binary versions available for install on this host."""
        return self._request("GET", "/panel/api/server/getXrayVersion", error_msg="Failed to get xray versions")

    def get_panel_update_info(self) -> XUIResponse:
        """Check whether a newer 3x-ui release is available on GitHub."""
        return self._request("GET", "/panel/api/server/getPanelUpdateInfo", error_msg="Failed to get panel update info")

    def get_config_json(self) -> XUIResponse:
        """Return the assembled Xray config that's currently running on this host."""
        return self._request("GET", "/panel/api/server/getConfigJson", error_msg="Failed to get config json")

    def get_new_uuid(self) -> XUIResponse:
        """Generate a fresh UUID v4. Convenience helper for client IDs."""
        return self._request("GET", "/panel/api/server/getNewUUID", error_msg="Failed to generate UUID")

    def get_new_x25519_cert(self) -> XUIResponse:
        """Generate a new X25519 keypair for Reality."""
        return self._request("GET", "/panel/api/server/getNewX25519Cert", error_msg="Failed to generate X25519 cert")

    def get_new_mldsa65(self) -> XUIResponse:
        """Generate a new ML-DSA-65 keypair (post-quantum signature). Returns privateKey, publicKey, seed."""
        return self._request("GET", "/panel/api/server/getNewmldsa65", error_msg="Failed to generate ML-DSA-65 keypair")

    def get_new_mlkem768(self) -> XUIResponse:
        """Generate a new ML-KEM-768 keypair (post-quantum KEM). Returns clientKey, serverKey."""
        return self._request("GET", "/panel/api/server/getNewmlkem768", error_msg="Failed to generate ML-KEM-768 keypair")

    def get_new_vless_enc(self) -> XUIResponse:
        """Generate VLESS encryption auth options. Returns an auths array with id, label, encryption, decryption."""
        return self._request("GET", "/panel/api/server/getNewVlessEnc", error_msg="Failed to generate VLESS encryption")

    def get_logs(self, count: int) -> XUIResponse:
        """Return the last N lines of the panel's own log."""
        return self._request("POST", f"/panel/api/server/logs/{count}", error_msg="Failed to get panel logs")

    def get_xray_logs(self, count: int) -> XUIResponse:
        """Return the last N lines of the Xray process log."""
        return self._request("POST", f"/panel/api/server/xraylogs/{count}", error_msg="Failed to get xray logs")

    # =============== SETTINGS ===============
    def get_all_settings(self) -> XUIResponse:
        """Return every panel setting: web server, Telegram bot, subscription, security, LDAP."""
        return self._request("POST", "/panel/api/setting/all", error_msg="Failed to get settings")

    def get_default_settings(self) -> XUIResponse:
        """Return the computed default settings based on the request host."""
        return self._request("POST", "/panel/api/setting/defaultSettings", error_msg="Failed to get default settings")

    def get_factory_defaults(self) -> XUIResponse:
        """Return the shipped factory default value per browser-safe setting key."""
        return self._request("POST", "/panel/api/setting/factoryDefaults", error_msg="Failed to get factory defaults")

    def get_default_json_config(self) -> XUIResponse:
        """Return the built-in default Xray JSON config template that ships with this panel version."""
        return self._request("GET", "/panel/api/setting/getDefaultJsonConfig", error_msg="Failed to get default json config")

    def validate_regex(self, pattern: str) -> XUIResponse:
        """Validate a regular expression with the backend Go RE2 compiler without saving it."""
        if not pattern:
            raise XUIValidationError("pattern must not be empty")
        return self._request("POST", "/panel/api/setting/validateRegex", json_data={"regex": pattern}, error_msg="Failed to validate regex")

    # =============== API TOKENS ===============
    def get_api_tokens(self) -> XUIResponse:
        """List every API token, enabled or not. The token value itself is never returned, only metadata."""
        return self._request("GET", "/panel/api/setting/apiTokens", error_msg="Failed to get API tokens")

    def create_api_token(self, name: str) -> XUIResponse:
        """Mint a new API token."""
        if not (1 <= len(name) <= 64):
            raise XUIValidationError("Token name must be between 1 and 64 characters")
        return self._request("POST", "/panel/api/setting/apiTokens/create", json_data={"name": name}, error_msg="Failed to create API token")

    def delete_api_token(self, token_id: int) -> XUIResponse:
        """Permanently delete a token. Any caller using it stops authenticating immediately."""
        return self._request("POST", f"/panel/api/setting/apiTokens/delete/{token_id}", error_msg=f"Failed to delete API token {token_id}")

    def set_api_token_enabled(self, token_id: int, enabled: bool) -> XUIResponse:
        """Toggle a token enabled/disabled without deleting it."""
        return self._request("POST", f"/panel/api/setting/apiTokens/setEnabled/{token_id}", json_data={"enabled": enabled}, error_msg=f"Failed to set enabled on API token {token_id}")

    # =============== XRAY SETTINGS ===============
    def get_xray_settings(self) -> XUIResponse:
        """Return the Xray config template, available inbound tags, client reverse tags, and outbound test URL."""
        return self._request("POST", "/panel/api/xray/", error_msg="Failed to get xray settings")

    def get_default_xray_json_config(self) -> XUIResponse:
        """Return the built-in default Xray config shipped with the panel."""
        return self._request("GET", "/panel/api/xray/getDefaultJsonConfig", error_msg="Failed to get default xray json config")

    def get_outbounds_traffic(self) -> XUIResponse:
        """Return traffic statistics for every outbound (up/down/total counters)."""
        return self._request("GET", "/panel/api/xray/getOutboundsTraffic", error_msg="Failed to get outbounds traffic")

    def get_xray_result(self) -> XUIResponse:
        """Return the most recent Xray process stdout/stderr output."""
        return self._request("GET", "/panel/api/xray/getXrayResult", error_msg="Failed to get xray result")

    def reset_outbound_traffic(self, tag: str) -> XUIResponse:
        """Reset traffic counters for a specific outbound by tag."""
        if not tag:
            raise XUIValidationError("tag must not be empty")
        return self._request("POST", "/panel/api/xray/resetOutboundsTraffic", json_data={"tag": tag}, error_msg=f"Failed to reset traffic for outbound {tag}")

    def get_outbound_subs(self) -> XUIResponse:
        """List all outbound subscriptions, newest first."""
        return self._request("GET", "/panel/api/xray/outbound-subs", error_msg="Failed to get outbound subs")

    def preview_outbound_sub(self, url: str) -> XUIResponse:
        """Preview a subscription URL: fetch and parse it into outbounds without persisting anything."""
        if not url:
            raise XUIValidationError("url must not be empty")
        return self._request("POST", "/panel/api/xray/outbound-subs/parse", json_data={"url": url}, error_msg="Failed to preview outbound sub")