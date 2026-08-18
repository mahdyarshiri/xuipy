import requests
from xuipy.exceptions import XUIAuthError, XUIRequestError

class XUI:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._login()

    def _login(self):
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/login",
            json={
                "username": self.username,
                "password": self.password,
            },
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIAuthError(f"Login failed: {data.get('msg', 'unknown error')}")

    def _get_csrf_token(self) -> str:
        response = self.session.get(f"{self.base_url}/csrf-token")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIAuthError(f"Failed to get CSRF token: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def logout(self):
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Logout failed: {data.get('msg', 'unknown error')}")
        return data

    def get_two_factor_enable(self):
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/getTwoFactorEnable",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to check 2FA status: {data.get('msg', 'unknown error')}")
        return data.get("obj")
    
    def get_inbounds(self):
        """List every inbound owned by the authenticated user, including clientStats traffic counters."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/list")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get inbounds: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def get_inbounds_slim(self):
        """Same as get_inbounds but with client details stripped down. Use for list pages."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/list/slim")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get slim inbounds: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def get_inbound_options(self):
        """Lightweight picker projection (id, remark, tag, protocol, port). Use for dropdowns."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/options")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get inbound options: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def get_all_links(self):
        """Return every protocol URL (vless://, vmess://, etc.) across all inbounds and clients."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/allLinks")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get all links: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def get_inbound(self, inbound_id: int):
        """Fetch a single inbound by numeric ID."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/get/{inbound_id}")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def add_inbound(self, inbound_data: dict):
        """Create a new inbound. inbound_data must include protocol, port, settings, streamSettings, sniffing, remark."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/add",
            json=inbound_data,
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to add inbound: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def update_inbound(self, inbound_id: int, inbound_data: dict):
        """Replace an inbound's configuration. Body shape mirrors add_inbound."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/update/{inbound_id}",
            json=inbound_data,
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to update inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def delete_inbound(self, inbound_id: int):
        """Delete an inbound by ID. Also removes its associated client stats rows."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/del/{inbound_id}",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to delete inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data

    def bulk_delete_inbounds(self, inbound_ids: list):
        """Delete many inbounds in one call. Failures are reported per id."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/bulkDel",
            json=inbound_ids,
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to bulk delete inbounds: {data.get('msg', 'unknown error')}")
        return data

    def set_inbound_enable(self, inbound_id: int, enable: bool):
        """Toggle only the enable flag without re-serialising the whole settings JSON."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/setEnable/{inbound_id}",
            json={"enable": enable},
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to set enable on inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data

    def reset_inbound_traffic(self, inbound_id: int):
        """Zero out upload + download counters for a single inbound."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/{inbound_id}/resetTraffic",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to reset traffic for inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data

    def reset_all_traffics(self):
        """Reset upload + download counters on every inbound. Destructive."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/resetAllTraffics",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to reset all traffics: {data.get('msg', 'unknown error')}")
        return data

    def delete_all_clients(self, inbound_id: int):
        """Remove every client attached to a single inbound while keeping the inbound itself. Destructive."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/{inbound_id}/delAllClients",
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to delete all clients on inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data

    def get_fallbacks(self, inbound_id: int):
        """List the fallback rules attached to a master VLESS/Trojan TCP-TLS inbound."""
        response = self.session.get(f"{self.base_url}/panel/api/inbounds/{inbound_id}/fallbacks")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to get fallbacks for inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data["obj"]

    def set_fallbacks(self, inbound_id: int, fallbacks: list):
        """Replace the entire fallback list for a master inbound. Triggers an Xray restart."""
        csrf_token = self._get_csrf_token()
        response = self.session.post(
            f"{self.base_url}/panel/api/inbounds/{inbound_id}/fallbacks",
            json=fallbacks,
            headers={"X-CSRF-Token": csrf_token},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise XUIRequestError(f"Failed to set fallbacks for inbound {inbound_id}: {data.get('msg', 'unknown error')}")
        return data