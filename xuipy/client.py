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
    
    