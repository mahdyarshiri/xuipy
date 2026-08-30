from typing import Any, Dict, List, Optional, Union
import requests

from xuipy.exceptions import XUIAuthError, XUIRequestError

XUIResponse = Union[Dict[str, Any], List[Any], str, bool]


class RequestHandler:
    """Core HTTP request handling."""

    def _request(self, method: str, path: str, json_data: Optional[dict] = None, params: Optional[dict] = None, error_msg: str = "Request failed", _retry_auth: bool = True, _retry_csrf: bool = True,) -> XUIResponse:
        headers = {}
        using_bearer = "Authorization" in self.session.headers
        if method.upper() != "GET" and not using_bearer:
            headers["X-CSRF-Token"] = self._get_csrf_token()
        try:
            response = self.session.request(method, f"{self.base_url}{path}", json=json_data, params=params, headers=headers, timeout=self.timeout,)
        except requests.RequestException as e:
            raise XUIRequestError(f"{error_msg}: {e}") from e

        # If a cached CSRF token was stale, refresh it once and retry
        if response.status_code == 403 and not using_bearer and method.upper() != "GET" and _retry_csrf:
            headers["X-CSRF-Token"] = self._get_csrf_token(force_refresh=True)
            try:
                response = self.session.request(method, f"{self.base_url}{path}", json=json_data, params=params, headers=headers, timeout=self.timeout,)
            except requests.RequestException as e:
                raise XUIRequestError(f"{error_msg}: {e}") from e

        # If the session cookie itself expired (not just the CSRF token), and we were
        # authenticated via username/password, transparently re-login once and retry
        # the original request. Bearer-token auth and the /login call itself never
        # attempt this, to avoid recursing on genuinely bad credentials.
        if response.status_code in (401, 403):
            if not using_bearer and _retry_auth and hasattr(self, "username"):
                with self._auth_lock:
                    self._login()
                return self._request(method, path, json_data=json_data, params=params, error_msg=error_msg, _retry_auth=False, _retry_csrf=_retry_csrf,)
            raise XUIAuthError(f"{error_msg}: authentication failed (HTTP {response.status_code})")

        # Try to parse the panel's JSON body first so a 4xx/5xx with a useful
        # "msg" field isn't swallowed by raise_for_status() before we can read it.
        try:
            data = response.json()
        except ValueError as e:
            try:
                response.raise_for_status()
            except requests.RequestException as http_err:
                raise XUIRequestError(f"{error_msg}: {http_err}") from http_err
            raise XUIRequestError(f"{error_msg}: {e}") from e

        if not data.get("success"):
            raise XUIRequestError(f"{error_msg}: {data.get('msg', 'unknown error')}")

        if data.get("obj") is not None:
            return data.get("obj")
        return data.get("msg") or True