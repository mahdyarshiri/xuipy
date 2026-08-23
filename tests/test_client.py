import pytest
from xuipy.exceptions import XUIAuthError, XUIRequestError, XUIValidationError


def test_get_inbounds(mock_panel):
    panel, m = mock_panel
    m.get(
        "http://fake-panel.test/panel/api/inbounds/list",
        json={"success": True, "obj": [{"id": 1, "remark": "test", "port": 443}]},
    )
    result = panel.get_inbounds()
    assert result == [{"id": 1, "remark": "test", "port": 443}]


def test_get_inbound(mock_panel):
    panel, m = mock_panel
    m.get(
        "http://fake-panel.test/panel/api/inbounds/get/1",
        json={"success": True, "obj": {"id": 1, "remark": "test"}},
    )
    result = panel.get_inbound(1)
    assert result["id"] == 1


def test_add_inbound_success(mock_panel):
    panel, m = mock_panel
    m.post(
        "http://fake-panel.test/panel/api/inbounds/add",
        json={"success": True, "obj": {"id": 5, "remark": "new"}},
    )
    result = panel.add_inbound({"remark": "new", "port": 1000})
    assert result["id"] == 5


def test_add_inbound_missing_remark_raises_locally(mock_panel):
    panel, m = mock_panel
    with pytest.raises(XUIValidationError):
        panel.add_inbound({"port": 1000})  # no remark
    # confirm NO request was actually sent
    assert not any(
        req.path == "/panel/api/inbounds/add" for req in m.request_history
    )


def test_get_client(mock_panel):
    panel, m = mock_panel
    m.get(
        "http://fake-panel.test/panel/api/clients/get/testuser",
        json={"success": True, "obj": {"client": {"email": "testuser"}}},
    )
    result = panel.get_client("testuser")
    assert result["client"]["email"] == "testuser"


def test_add_client_default_inbound_ids(mock_panel):
    panel, m = mock_panel
    m.get(
        "http://fake-panel.test/panel/api/inbounds/options",
        json={"success": True, "obj": [{"id": 1, "remark": "a"}, {"id": 2, "remark": "b"}]},
    )
    m.post(
        "http://fake-panel.test/panel/api/clients/add",
        json={"success": True, "msg": "Client added.", "obj": None},
    )
    result = panel.add_client("newuser")
    sent_body = m.request_history[-1].json()
    assert sent_body["inboundIds"] == [1, 2]
    assert result == "Client added."


def test_add_client_empty_email_raises_locally(mock_panel):
    panel, m = mock_panel
    with pytest.raises(XUIValidationError):
        panel.add_client("")


def test_update_client_gb_conversion(mock_panel):
    panel, m = mock_panel
    m.post(
        "http://fake-panel.test/panel/api/clients/update/testuser",
        json={"success": True, "msg": "Updated.", "obj": None},
    )
    panel.update_client("testuser", total_gb=5)
    sent_body = m.request_history[-1].json()
    assert sent_body["totalGB"] == 5 * 1024 * 1024 * 1024


def test_request_failure_raises_request_error(mock_panel):
    panel, m = mock_panel
    m.get(
        "http://fake-panel.test/panel/api/inbounds/list",
        json={"success": False, "msg": "Something broke"},
    )
    with pytest.raises(XUIRequestError):
        panel.get_inbounds()


def test_auth_error_on_403(mock_panel):
    panel, m = mock_panel
    m.get("http://fake-panel.test/panel/api/inbounds/list", status_code=403)
    with pytest.raises(XUIAuthError):
        panel.get_inbounds()


def test_create_api_token_validation(mock_panel):
    panel, m = mock_panel
    with pytest.raises(XUIValidationError):
        panel.create_api_token("")
    with pytest.raises(XUIValidationError):
        panel.create_api_token("x" * 65)