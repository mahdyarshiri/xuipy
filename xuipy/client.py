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