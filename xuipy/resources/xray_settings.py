from xuipy.exceptions import XUIValidationError


class XraySettingsMixin:
    """Xray configuration methods."""

    def get_xray_settings(self):
        """Return the Xray config template, available inbound tags, client reverse tags, and outbound test URL."""
        return self._request("POST", "/panel/api/xray/", error_msg="Failed to get xray settings")

    def get_default_xray_json_config(self):
        """Return the built-in default Xray config shipped with the panel."""
        return self._request("GET", "/panel/api/xray/getDefaultJsonConfig", error_msg="Failed to get default xray json config")

    def get_outbounds_traffic(self):
        """Return traffic statistics for every outbound (up/down/total counters)."""
        return self._request("GET", "/panel/api/xray/getOutboundsTraffic", error_msg="Failed to get outbounds traffic")

    def get_xray_result(self):
        """Return the most recent Xray process stdout/stderr output."""
        return self._request("GET", "/panel/api/xray/getXrayResult", error_msg="Failed to get xray result")

    def reset_outbound_traffic(self, tag: str):
        """Reset traffic counters for a specific outbound by tag."""
        if not tag:
            raise XUIValidationError("tag must not be empty")
        return self._request("POST", "/panel/api/xray/resetOutboundsTraffic", json_data={"tag": tag}, error_msg=f"Failed to reset traffic for outbound {tag}")

    def get_outbound_subs(self):
        """List all outbound subscriptions, newest first."""
        return self._request("GET", "/panel/api/xray/outbound-subs", error_msg="Failed to get outbound subs")

    def preview_outbound_sub(self, url: str):
        """Preview a subscription URL: fetch and parse it into outbounds without persisting anything."""
        if not url:
            raise XUIValidationError("url must not be empty")
        return self._request("POST", "/panel/api/xray/outbound-subs/parse", json_data={"url": url}, error_msg="Failed to preview outbound sub")