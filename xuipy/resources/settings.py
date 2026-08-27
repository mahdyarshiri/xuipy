from xuipy.exceptions import XUIValidationError


class SettingsMixin:
    """Panel settings methods."""

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
        if not pattern:
            raise XUIValidationError("pattern must not be empty")
        return self._request("POST", "/panel/api/setting/validateRegex", json_data={"regex": pattern}, error_msg="Failed to validate regex")