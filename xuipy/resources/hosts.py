from xuipy.exceptions import XUIValidationError


class HostsMixin:
    """Host-related methods."""

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
        if not host_data:
            raise XUIValidationError("host_data must not be empty")
        return self._request("POST", "/panel/api/hosts/add", json_data=host_data, error_msg="Failed to add host")

    def update_host(self, group_id: str, host_data: dict):
        """Replace a host group's content."""
        if not group_id:
            raise XUIValidationError("group_id must not be empty")
        if not host_data:
            raise XUIValidationError("host_data must not be empty")
        return self._request("POST", f"/panel/api/hosts/update/{group_id}", json_data=host_data, error_msg=f"Failed to update host {group_id}")

    def delete_host(self, group_id: str):
        """Delete a host group."""
        return self._request("POST", f"/panel/api/hosts/del/{group_id}", error_msg=f"Failed to delete host {group_id}")

    def set_host_enable(self, group_id: str, enable: bool):
        """Enable or disable a host group."""
        return self._request("POST", f"/panel/api/hosts/setEnable/{group_id}", json_data={"enable": enable}, error_msg=f"Failed to set enable on host {group_id}")

    def reorder_hosts(self, group_ids: list):
        """Set host group sort order by the position of each groupId in the array."""
        if not group_ids:
            raise XUIValidationError("group_ids must not be empty")
        return self._request("POST", "/panel/api/hosts/reorder", json_data={"groupIds": group_ids}, error_msg="Failed to reorder hosts")