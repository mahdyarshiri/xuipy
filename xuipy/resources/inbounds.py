from xuipy.exceptions import XUIValidationError


class Inbounds:
    """Inbound-related methods."""

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
        if not inbound_data.get("remark"):
            raise XUIValidationError("inbound_data must include a non-empty 'remark'")
        if not inbound_data.get("port"):
            raise XUIValidationError("inbound_data must include a 'port'")
        return self._request("POST", "/panel/api/inbounds/add", json_data=inbound_data, error_msg="Failed to add inbound")

    def update_inbound(self, inbound_id: int, inbound_data: dict):
        """Replace an inbound's configuration. Body shape mirrors add_inbound."""
        if not inbound_data.get("remark"):
            raise XUIValidationError("inbound_data must include a non-empty 'remark'")
        if not inbound_data.get("port"):
            raise XUIValidationError("inbound_data must include a 'port'")
        return self._request("POST", f"/panel/api/inbounds/update/{inbound_id}", json_data=inbound_data, error_msg=f"Failed to update inbound {inbound_id}")

    def delete_inbound(self, inbound_id: int):
        """Delete an inbound by ID. Also removes its associated client stats rows."""
        return self._request("POST", f"/panel/api/inbounds/del/{inbound_id}", error_msg=f"Failed to delete inbound {inbound_id}")

    def bulk_delete_inbounds(self, inbound_ids: list):
        """Delete many inbounds in one call. Failures are reported per id."""
        if not inbound_ids:
            raise XUIValidationError("inbound_ids must not be empty")
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
        return self._request("POST", f"/panel/api/inbounds/{inbound_id}/fallbacks", json_data={"fallbacks": fallbacks}, error_msg=f"Failed to set fallbacks for inbound {inbound_id}",)