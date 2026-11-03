"""Only the desktop app's browser origins may call the server."""

import pytest

server = pytest.importorskip("services.moza_server.main")
from fastapi.testclient import TestClient  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402

# No `with` block: the startup hook (camera worker) must not run in tests.
client = TestClient(server.app)
APP_ORIGIN = "tauri://localhost"
EVIL_ORIGIN = "https://evil.example"


def test_app_origin_may_read_config():
    resp = client.get("/config", headers={"Origin": APP_ORIGIN})
    assert resp.headers.get("access-control-allow-origin") == APP_ORIGIN


def test_other_sites_get_no_cors_grant():
    resp = client.get("/config", headers={"Origin": EVIL_ORIGIN})
    assert "access-control-allow-origin" not in resp.headers


def test_other_sites_cannot_preflight_config_changes():
    resp = client.options(
        "/config",
        headers={"Origin": EVIL_ORIGIN, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"},
    )
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


def test_websocket_rejects_other_sites():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/telemetry", headers={"Origin": EVIL_ORIGIN}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


@pytest.mark.parametrize("headers", [{"Origin": APP_ORIGIN}, {}])
def test_websocket_accepts_app_and_non_browser_clients(headers):
    with client.websocket_connect("/ws/telemetry", headers=headers):
        pass
