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
        data = self._request("GET", "/panel/api/inbounds/list", error_msg="Failed to get inbounds")
        return data["obj"]

    def get_inbounds_slim(self):
        """Same as get_inbounds but with client details stripped down. Use for list pages."""
        data = self._request("GET", "/panel/api/inbounds/list/slim", error_msg="Failed to get slim inbounds")
        return data["obj"]

    def get_inbound_options(self):
        """Lightweight picker projection (id, remark, tag, protocol, port). Use for dropdowns."""
        data = self._request("GET", "/panel/api/inbounds/options", error_msg="Failed to get inbound options")
        return data["obj"]

    def get_all_links(self):
        """Return every protocol URL (vless://, vmess://, etc.) across all inbounds and clients."""
        data = self._request("GET", "/panel/api/inbounds/allLinks", error_msg="Failed to get all links")
        return data["obj"]

    def get_inbound(self, inbound_id: int):
        """Fetch a single inbound by numeric ID."""
        data = self._request("GET", f"/panel/api/inbounds/get/{inbound_id}", error_msg=f"Failed to get inbound {inbound_id}")
        return data["obj"]

    def add_inbound(self, inbound_data: dict):
        """Create a new inbound. inbound_data must include protocol, port, settings, streamSettings, sniffing, remark."""
        data = self._request("POST", "/panel/api/inbounds/add", json_data=inbound_data, error_msg="Failed to add inbound")
        return data["obj"]

    def update_inbound(self, inbound_id: int, inbound_data: dict):
        """Replace an inbound's configuration. Body shape mirrors add_inbound."""
        data = self._request("POST", f"/panel/api/inbounds/update/{inbound_id}", json_data=inbound_data, error_msg=f"Failed to update inbound {inbound_id}")
        return data["obj"]

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
        data = self._request("GET", f"/panel/api/inbounds/{inbound_id}/fallbacks", error_msg=f"Failed to get fallbacks for inbound {inbound_id}")
        return data["obj"]

    def set_fallbacks(self, inbound_id: int, fallbacks: list):
        """Replace the entire fallback list for a master inbound. Triggers an Xray restart."""
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/fallbacks", json_data={"fallbacks": fallbacks}, error_msg=f"Failed to set fallbacks for inbound {inbound_id}")