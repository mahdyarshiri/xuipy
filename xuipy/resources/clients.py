import time
from xuipy.exceptions import XUIValidationError


class ClientsMixin:
    """Client-related methods."""

    @staticmethod
    def _expiry_ms(expiry_days: int) -> int:
        """Convert a relative day count into an absolute epoch-ms expiry, or 0 for 'never expires'."""
        if expiry_days == 0:
            return 0
        return int(time.time() * 1000) + (expiry_days * 1000 * 60 * 60 * 24)

    def get_clients(self):
        """List every client with its attached inbound IDs and traffic record."""
        return self._request("GET", "/panel/api/clients/list", error_msg="Failed to get clients")

    def get_clients_paged(self, **params):
        """Filter, sort, and paginate clients on the server. Pass query params like page, size, search."""
        return self._request("GET", "/panel/api/clients/list/paged", params=params, error_msg="Failed to get paged clients")

    def get_client(self, email: str):
        """Fetch one client by email, including its attached inbound IDs."""
        return self._request("GET", f"/panel/api/clients/get/{email}", error_msg=f"Failed to get client {email}")

    def add_client(self, email: str, inbound_ids: list = None, enable: bool = True, expiry_days: int = 0, total_gb: float = 0, tg_id: int = 0, limit_ip: int = 0, flow: str = "", comment: str = "", group: str = "",):
        """Create a new client and attach it to one or more inbounds.
        Per-protocol secrets (uuid, password, auth) are generated server-side.

        email: unique identifier for the client
        inbound_ids: inbounds to attach to. Defaults to ALL current inbounds if not given.
        enable: whether the client is active on creation
        expiry_days: days from now until expiry, 0 = never expires
        total_gb: traffic quota in GB, 0 = unlimited
        tg_id: linked Telegram user ID, 0 = none
        limit_ip: max simultaneous IPs, 0 = unlimited
        flow: XTLS flow (e.g. 'xtls-rprx-vision'), empty = none
        comment: optional note shown in the panel UI
        group: client group label, empty = no group
        """
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
            "limitIp": limit_ip,
            "flow": flow,
            "comment": comment,
            "group": group,
        }
        return self._request("POST", "/panel/api/clients/add", json_data={"client": client_data, "inboundIds": inbound_ids}, error_msg="Failed to add client",)

    def update_client(self, email: str, enable: bool = True, expiry_days: int = 0, total_gb: float = 0, tg_id: int = 0, limit_ip: int = 0, flow: str = "", comment: str = "", group: str = "",):
        """Update an existing client by email. Replaces the full row — pass all fields you want kept.

        email: the client's email/identifier
        enable: whether the client is active
        expiry_days: days from now until expiry, 0 = never expires
        total_gb: traffic quota in GB, 0 = unlimited
        tg_id: linked Telegram user ID, 0 = none
        limit_ip: max simultaneous IPs, 0 = unlimited
        flow: XTLS flow (e.g. 'xtls-rprx-vision'), empty = none
        comment: optional note shown in the panel UI
        group: client group label, empty = no group
        """
        if not email:
            raise XUIValidationError("email must not be empty")

        client_data = {
            "email": email,
            "enable": enable,
            "expiryTime": self._expiry_ms(expiry_days),
            "totalGB": int(total_gb * 1024 * 1024 * 1024),
            "tgId": tg_id,
            "limitIp": limit_ip,
            "flow": flow,
            "comment": comment,
            "group": group,
        }
        return self._request("POST", f"/panel/api/clients/update/{email}", json_data=client_data, error_msg=f"Failed to update client {email}")

    def delete_client(self, email: str, keep_traffic: bool = False):
        """Delete a client by email. Set keep_traffic=True to retain its traffic record."""
        if not email:
            raise XUIValidationError("email must not be empty")
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