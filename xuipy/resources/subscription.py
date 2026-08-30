import requests
from xuipy.exceptions import XUIValidationError, XUIRequestError


class Subscription:
    """Subscription-server methods."""

    def get_subscription(self, sub_url: str, format: str = "normal"):
        """Fetch a client's subscription in the given format.

        sub_url: the full subscription URL for this format (host/port/path vary per panel setup)
        format: "normal" (default) = base64-encoded links as plain text
                "json" = list of proxy config objects
                "clash" = Clash/Mihomo-compatible YAML text
        """
        if not sub_url:
            raise XUIValidationError("sub_url must not be empty")
        try:
            response = requests.get(sub_url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise XUIRequestError(f"Failed to get subscription: {e}") from e

        if format == "json":
            return response.json()
        return response.text