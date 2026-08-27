from xuipy.exceptions import XUIValidationError


class NodesMixin:
    """Node-related methods."""

    def get_nodes(self):
        """List every configured node with its connection details, health, and last heartbeat."""
        return self._request("GET", "/panel/api/nodes/list", error_msg="Failed to get nodes")

    def get_node(self, node_id: int):
        """Fetch a single node by ID."""
        return self._request("GET", f"/panel/api/nodes/get/{node_id}", error_msg=f"Failed to get node {node_id}")

    def add_node(self, url: str, api_token: str, remark: str = "", allow_private_address: bool = False):
        """Register a new remote node."""
        if not url:
            raise XUIValidationError("url must not be empty")
        if not api_token:
            raise XUIValidationError("api_token must not be empty")
        node_data = {
            "url": url,
            "apiToken": api_token,
            "remark": remark,
            "allowPrivateAddress": allow_private_address,
        }
        return self._request("POST", "/panel/api/nodes/add", json_data=node_data, error_msg="Failed to add node")

    def update_node(self, node_id: int, node_data: dict):
        """Replace a node's connection details. Omit apiToken to keep the stored token, or set clearApiToken=True to clear it."""
        if not node_data:
            raise XUIValidationError("node_data must not be empty")
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