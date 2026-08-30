from xuipy.exceptions import XUIAuthError


class Auth:
    """Authentication-related methods."""

    def _get_csrf_token(self, force_refresh: bool = False) -> str:
        """Return the cached CSRF token, fetching a fresh one if not cached or force_refresh=True."""
        if self._csrf_token is not None and not force_refresh:
            return self._csrf_token

        with self._csrf_lock:
            if self._csrf_token is not None and not force_refresh:
                return self._csrf_token

            try:
                response = self.session.get(f"{self.base_url}/csrf-token", timeout=self.timeout)
            except Exception as e:
                from xuipy.exceptions import XUIRequestError
                raise XUIRequestError(f"Failed to get CSRF token: {e}") from e
            if response.status_code in (401, 403):
                raise XUIAuthError(f"Failed to get CSRF token: authentication failed (HTTP {response.status_code})")
            try:
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                from xuipy.exceptions import XUIRequestError
                raise XUIRequestError(f"Failed to get CSRF token: {e}") from e

            if not data.get("success"):
                raise XUIAuthError(f"Failed to get CSRF token: {data.get('msg', 'unknown error')}")

            self._csrf_token = data["obj"]
            return self._csrf_token

    def _login(self):
        """Authenticate with username + password and receive a session cookie."""
        return self._request("POST", "/login", json_data={"username": self.username, "password": self.password}, error_msg="Login failed", _retry_auth=False,)

    def logout(self):
        """Clear the session cookie."""
        return self._request("POST", "/logout", error_msg="Logout failed")

    def get_two_factor_enable(self):
        """Return whether 2FA is enabled on the panel."""
        return self._request("POST", "/getTwoFactorEnable", error_msg="Failed to check 2FA status")