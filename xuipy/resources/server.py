class Server:
    """Server-related methods."""

    def get_server_status(self):
        """Real-time machine snapshot: CPU, memory, swap, disk, network IO, load averages, Xray state."""
        return self._request("GET", "/panel/api/server/status", error_msg="Failed to get server status")

    def get_fail2ban_status(self):
        """Reports whether per-client IP limits can be enforced on this host."""
        return self._request("GET", "/panel/api/server/fail2banStatus", error_msg="Failed to get fail2ban status")

    def get_server_history(self, metric: str, bucket: str):
        """Aggregated time-series for one metric over the last ~6 hours.

        bucket: interval size in seconds as a string, e.g. "60" for 1-minute buckets.
        """
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