import time
import requests
from xuipy.exceptions import XUIRequestError

class XUI:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._login()

    # =============== REQUEST HANDLING ===============
    def _request(self, method: str, path: str, json_data: dict = None, params: dict = None, error_msg: str = "Request failed"):
        headers = {}
        if method.upper() != "GET":
            headers["X-CSRF-Token"] = self._get_csrf_token()
        try:
            response = self.session.request(method, f"{self.base_url}{path}", json=json_data, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise XUIRequestError(f"{error_msg}: {e}") from e

        if not data.get("success"):
            raise XUIRequestError(f"{error_msg}: {data.get('msg', 'unknown error')}")
        return data

    # =============== AUTHENTICATION ===============
    def _get_csrf_token(self) -> str:
        """Mint a CSRF token for the current session, required on unsafe (POST) requests."""
        response = self.session.get(f"{self.base_url}/csrf-token")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get CSRF token: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def _login(self):
        """Authenticate with username + password and receive a session cookie."""
        return self._request("POST", "/login", json_data={"username": self.username, "password": self.password}, error_msg="Login failed")

    def logout(self):
        """Clear the session cookie."""
        return self._request("POST", "/logout", error_msg="Logout failed")

    def get_two_factor_enable(self):
        """Return whether 2FA is enabled on the panel."""
        data = self._request("POST", "/getTwoFactorEnable", error_msg="Failed to check 2FA status")
        return data.get("obj")

    # =============== INBOUNDS ===============
    def get_inbounds(self):
        """List every inbound owned by the authenticated user, including clientStats traffic counters."""
        return self._request("GET", "/panel/api/inbounds/list", error_msg="Failed to get inbounds")

    def get_inbounds_slim(self):
        """Same as get_inbounds but with client details stripped down. Use for list pages."""
        return self._request("GET", "/panel/api/inbounds/list/slim", error_msg="Failed to get slim inbounds")

    def get_inbound_options(self):
        """Lightweight picker projection (id, remark, tag, protocol, port). Use for dropdowns."""
        return self._request("GET", "/panel/api/inbounds/options", error_msg="Failed to get inbound options")

    def get_all_links(self):
        """Return every protocol URL (vless://, vmess://, etc.) across all inbounds and clients."""
        return self._request("GET", "/panel/api/inbounds/allLinks", error_msg="Failed to get all links")

    def get_inbound(self, inbound_id: int):
        """Fetch a single inbound by numeric ID."""
        return self._request("GET", f"/panel/api/inbounds/get/{inbound_id}", error_msg=f"Failed to get inbound {inbound_id}")

    def add_inbound(self, inbound_data: dict):
        """Create a new inbound. inbound_data must include protocol, port, settings, streamSettings, sniffing, remark."""
        return self._request("POST", "/panel/api/inbounds/add", json_data=inbound_data, error_msg="Failed to add inbound")

    def update_inbound(self, inbound_id: int, inbound_data: dict):
        """Replace an inbound's configuration. Body shape mirrors add_inbound."""
        return self._request("POST", f"/panel/api/inbounds/update/{inbound_id}", json_data=inbound_data, error_msg=f"Failed to update inbound {inbound_id}")

    def delete_inbound(self, inbound_id: int):
        """Delete an inbound by ID. Also removes its associated client stats rows."""
        return self._request("POST", f"/panel/api/inbounds/del/{inbound_id}", error_msg=f"Failed to delete inbound {inbound_id}")

    def bulk_delete_inbounds(self, inbound_ids: list):
        """Delete many inbounds in one call. Failures are reported per id."""
        return self._request("POST", "/panel/api/inbounds/bulkDel", json_data={"ids": inbound_ids}, error_msg="Failed to bulk delete inbounds")

    def set_inbound_enable(self, inbound_id: int, enable: bool):
        """Toggle only the enable flag without re-serialising the whole settings JSON."""
        return self._request("POST", f"/panel/api/inbounds/setEnable/{inbound_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on inbound {inbound_id}")

    def reset_inbound_traffic(self, inbound_id: int):
        """Zero out upload + download counters for a single inbound."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/resetTraffic", error_msg=f"Failed to reset traffic for inbound {inbound_id}")

    def reset_all_traffics(self):
        """Reset upload + download counters on every inbound. Destructive."""
        return self._request("POST", "/panel/api/inbounds/resetAllTraffics", error_msg="Failed to reset all traffics")

    def delete_all_clients(self, inbound_id: int):
        """Remove every client attached to a single inbound while keeping the inbound itself. Destructive."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/delAllClients", error_msg=f"Failed to delete all clients on inbound {inbound_id}")

    def get_fallbacks(self, inbound_id: int):
        """List the fallback rules attached to a master VLESS/Trojan TCP-TLS inbound."""
        return self._request("GET", f"/panel/api/inbounds/{inbound_id}/fallbacks", error_msg=f"Failed to get fallbacks for inbound {inbound_id}")

    def set_fallbacks(self, inbound_id: int, fallbacks: list):
        """Replace the entire fallback list for a master inbound. Triggers an Xray restart."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/fallbacks", json_data={"fallbacks": fallbacks}, error_msg=f"Failed to set fallbacks for inbound {inbound_id}")
    
    # =============== CLIENTS ===============
    def get_clients(self):
        """List every client with its attached inbound IDs and traffic record."""
        return self._request("GET", "/panel/api/clients/list", error_msg="Failed to get clients")

    def get_clients_paged(self, **params):
        """Filter, sort, and paginate clients on the server. Pass query params like page, size, search."""
        return self._request("GET", "/panel/api/clients/list/paged", params=params, error_msg="Failed to get paged clients")

    def get_client(self, email: str):
        """Fetch one client by email, including its attached inbound IDs."""
        return self._request("GET", f"/panel/api/clients/get/{email}", error_msg=f"Failed to get client {email}")

    def add_client(self, client_data: dict, inbound_ids: list):
        """Create a new client and attach it to one or more inbounds. Secrets (uuid/password) auto-generated if omitted."""
        return self._request("POST", "/panel/api/clients/add", json_data={"client": client_data, "inboundIds": inbound_ids}, error_msg="Failed to add client")

    def update_client(self, email: str, enable: bool = True, expiry: int = 0, total_gb: int = 0, tg_id: int = 0):
        """Update an existing client by email. Replaces the full row — pass all fields you want kept."""
        expiry_time = 0 if expiry == 0 else int(time.time() * 1000) + (expiry * 1000)
        data = {
            "email": email,
            "enable": enable,
            "expiryTime": expiry_time,
            "totalGB": int(total_gb * 1024 * 1024 * 1024),
            "tgId": tg_id,
        }
        return self._request("POST", f"/panel/api/clients/update/{email}", json_data=data, error_msg=f"Failed to update client {email}")

    def delete_client(self, email: str, keep_traffic: bool = False):
        """Delete a client by email. Set keep_traffic=True to retain its traffic record."""
        params = {"keepTraffic": 1} if keep_traffic else {}
        return self._request("POST", f"/panel/api/clients/del/{email}", params=params, error_msg=f"Failed to delete client {email}")

    def reset_client_traffic(self, email: str):
        """Zero out a single client's up/down counters and re-enable it if it was depleted."""
        return self._request("POST", f"/panel/api/clients/resetTraffic/{email}", error_msg=f"Failed to reset traffic for client {email}")

    def get_client_ips(self, email: str):
        """List source IPs that have connected with this client's credentials."""
        return self._request("POST", f"/panel/api/clients/ips/{email}", error_msg=f"Failed to get IPs for client {email}")

    def get_client_traffic(self, email: str):
        """Traffic counters for a client identified by email."""
        return self._request("GET", f"/panel/api/clients/traffic/{email}", error_msg=f"Failed to get traffic for client {email}")

    def get_client_links(self, email: str):
        """Return every share URL for one client across all attached inbounds."""
        return self._request("GET", f"/panel/api/clients/links/{email}", error_msg=f"Failed to get links for client {email}")

    # =============== NODES ===============
    def get_nodes(self):
        """List every configured node with its connection details, health, and last heartbeat."""
        return self._request("GET", "/panel/api/nodes/list", error_msg="Failed to get nodes")

    def get_node(self, node_id: int):
        """Fetch a single node by ID."""
        return self._request("GET", f"/panel/api/nodes/get/{node_id}", error_msg=f"Failed to get node {node_id}")

    def add_node(self, url: str, api_token: str, remark: str = "", allow_private_address: bool = False):
        """Register a new remote node."""
        node_data = {
            "url": url,
            "apiToken": api_token,
            "remark": remark,
            "allowPrivateAddress": allow_private_address,
        }
        return self._request("POST", "/panel/api/nodes/add", json_data=node_data, error_msg="Failed to add node")

    def update_node(self, node_id: int, node_data: dict):
        """Replace a node's connection details. Omit apiToken to keep the stored token, or set clearApiToken=True to clear it."""
        return self._request("POST", f"/panel/api/nodes/update/{node_id}", json_data=node_data, error_msg=f"Failed to update node {node_id}")

    def delete_node(self, node_id: int):
        """Delete a node. Inbounds bound to it are not auto-migrated."""
        return self._request("POST", f"/panel/api/nodes/del/{node_id}", error_msg=f"Failed to delete node {node_id}")

    def set_node_enable(self, node_id: int, enable: bool):
        """Pause or resume traffic sync with this node."""
        return self._request("POST", f"/panel/api/nodes/setEnable/{node_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on node {node_id}")

    def probe_node(self, node_id: int):
        """Probe an existing node, updating its cached health state."""
        return self._request("POST", f"/panel/api/nodes/probe/{node_id}", error_msg=f"Failed to probe node {node_id}")
    
    # =============== HOSTS ===============
    def get_hosts(self):
        """List every host across all inbounds, grouped by inbound then ordered by sort order."""
        return self._request("GET", "/panel/api/hosts/list", error_msg="Failed to get hosts")

    def get_host(self, group_id: str):
        """Fetch a single host group by Group ID."""
        return self._request("GET", f"/panel/api/hosts/get/{group_id}", error_msg=f"Failed to get host {group_id}")

    def get_hosts_by_inbound(self, inbound_id: int):
        """Fetch one inbound's hosts, grouped by host group."""
        return self._request("GET", f"/panel/api/hosts/byInbound/{inbound_id}", error_msg=f"Failed to get hosts for inbound {inbound_id}")

    def get_host_tags(self):
        """Distinct, sorted set of tags used across all hosts."""
        return self._request("GET", "/panel/api/hosts/tags", error_msg="Failed to get host tags")

    def add_host(self, host_data: dict):
        """Create a host group on inbounds."""
        return self._request("POST", "/panel/api/hosts/add", json_data=host_data, error_msg="Failed to add host")

    def update_host(self, group_id: str, host_data: dict):
        """Replace a host group's content."""
        return self._request("POST", f"/panel/api/hosts/update/{group_id}", json_data=host_data, error_msg=f"Failed to update host {group_id}")

    def delete_host(self, group_id: str):
        """Delete a host group."""
        return self._request("POST", f"/panel/api/hosts/del/{group_id}", error_msg=f"Failed to delete host {group_id}")

    def set_host_enable(self, group_id: str, enable: bool):
        """Enable or disable a host group."""
        return self._request("POST", f"/panel/api/hosts/setEnable/{group_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on host {group_id}")

    def reorder_hosts(self, group_ids: list):
        """Set host group sort order by the position of each groupId in the array."""
        return self._request("POST", "/panel/api/hosts/reorder", json_data={"groupIds": group_ids}, error_msg="Failed to reorder hosts")
    
    # =============== SERVER ===============
    def get_server_status(self):
        """Real-time machine snapshot: CPU, memory, swap, disk, network IO, load averages, Xray state."""
        return self._request("GET", "/panel/api/server/status", error_msg="Failed to get server status")

    def get_fail2ban_status(self):
        """Reports whether per-client IP limits can be enforced on this host."""
        return self._request("GET", "/panel/api/server/fail2banStatus", error_msg="Failed to get fail2ban status")

    def get_server_history(self, metric: str, bucket: str):
        """Aggregated time-series for one metric over the last ~6 hours. bucket: interval size in seconds as a string, e.g. "60" for 1-minute buckets."""
        return self._request("GET", f"/panel/api/server/history/{metric}/{bucket}", error_msg=f"Failed to get history for {metric}")
    
    def get_xray_metrics_state(self):
        """Xray runtime metrics state: whether metrics are configured and current snapshot values."""
        return self._request("GET", "/panel/api/server/xrayMetricsState", error_msg="Failed to get xray metrics state")

    def get_xray_version(self):
        """List Xray binary versions available for install on this host."""
        return self._request("GET", "/panel/api/server/getXrayVersion", error_msg="Failed to get xray versions")

    def get_panel_update_info(self):
        """Check whether a newer 3x-ui release is available on GitHub."""
        return self._request("GET", "/panel/api/server/getPanelUpdateInfo", error_msg="Failed to get panel update info")

    def get_config_json(self):
        """Return the assembled Xray config that's currently running on this host."""
        return self._request("GET", "/panel/api/server/getConfigJson", error_msg="Failed to get config json")

    def get_new_uuid(self):
        """Generate a fresh UUID v4. Convenience helper for client IDs."""
        return self._request("GET", "/panel/api/server/getNewUUID", error_msg="Failed to generate UUID")

    def get_new_x25519_cert(self):
        """Generate a new X25519 keypair for Reality."""
        return self._request("GET", "/panel/api/server/getNewX25519Cert", error_msg="Failed to generate X25519 cert")

    def get_new_mldsa65(self):
        """Generate a new ML-DSA-65 keypair (post-quantum signature). Returns privateKey, publicKey, seed."""
        return self._request("GET", "/panel/api/server/getNewmldsa65", error_msg="Failed to generate ML-DSA-65 keypair")

    def get_new_mlkem768(self):
        """Generate a new ML-KEM-768 keypair (post-quantum KEM). Returns clientKey, serverKey."""
        return self._request("GET", "/panel/api/server/getNewmlkem768", error_msg="Failed to generate ML-KEM-768 keypair")

    def get_new_vless_enc(self):
        """Generate VLESS encryption auth options. Returns an auths array with id, label, encryption, decryption."""
        return self._request("GET", "/panel/api/server/getNewVlessEnc", error_msg="Failed to generate VLESS encryption")

    def get_logs(self, count: int):
        """Return the last N lines of the panel's own log."""
        return self._request("POST", f"/panel/api/server/logs/{count}", error_msg="Failed to get panel logs")

    def get_xray_logs(self, count: int):
        """Return the last N lines of the Xray process log."""
        return self._request("POST", f"/panel/api/server/xraylogs/{count}", error_msg="Failed to get xray logs")
    
    # =============== SETTINGS ===============
    def get_all_settings(self):
        """Return every panel setting: web server, Telegram bot, subscription, security, LDAP."""
        return self._request("POST", "/panel/api/setting/all", error_msg="Failed to get settings")

    def get_default_settings(self):
        """Return the computed default settings based on the request host."""
        return self._request("POST", "/panel/api/setting/defaultSettings", error_msg="Failed to get default settings")

    def get_factory_defaults(self):
        """Return the shipped factory default value per browser-safe setting key."""
        return self._request("POST", "/panel/api/setting/factoryDefaults", error_msg="Failed to get factory defaults")

    def get_default_json_config(self):
        """Return the built-in default Xray JSON config template that ships with this panel version."""
        return self._request("GET", "/panel/api/setting/getDefaultJsonConfig", error_msg="Failed to get default json config")

    def validate_regex(self, pattern: str):
        """Validate a regular expression with the backend Go RE2 compiler without saving it."""
        return self._request("POST", "/panel/api/setting/validateRegex", json_data={"regex": pattern}, error_msg="Failed to validate regex")
    
    