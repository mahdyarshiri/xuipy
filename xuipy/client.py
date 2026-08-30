import threading
import requests

from typing import Optional
from xuipy.exceptions import XUIValidationError

from xuipy.core import RequestHandler, Auth
from xuipy.resources import Inbounds, Clients, Nodes, Hosts, Server, Settings, ApiTokens, XraySettings, Subscription

class XUI(RequestHandler, Auth, Inbounds, Clients, Nodes, Hosts, Server, Settings, ApiTokens, XraySettings, Subscription):
    """A Python client for the 3x-ui panel API."""

    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None, api_token: Optional[str] = None, timeout: int = 10,):
        if not base_url:
            raise XUIValidationError("base_url must not be empty")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._csrf_token: Optional[str] = None
        self._csrf_lock = threading.Lock()
        self._auth_lock = threading.Lock()

        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})
        elif username and password:
            self.username = username
            self.password = password
            self._login()
        else:
            raise XUIValidationError("Provide either (username and password) or api_token")

    def __enter__(self) -> "XUI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()