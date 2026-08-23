import pytest
import requests_mock
from xuipy.client import XUI


@pytest.fixture
def mock_panel():
    """A fully authenticated XUI client backed by requests_mock, no real network calls."""
    with requests_mock.Mocker() as m:
        m.get("http://fake-panel.test/csrf-token", json={"success": True, "obj": "fake-csrf-token"})
        m.post("http://fake-panel.test/login", json={"success": True, "obj": None})
        panel = XUI(base_url="http://fake-panel.test", username="admin", password="admin")
        yield panel, m