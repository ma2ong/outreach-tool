import app.main as main
import app.api.channels as ch
from app.browser_engine import FakeEngine
from fastapi.testclient import TestClient


def _client():
    ch.ENGINE = FakeEngine()
    return TestClient(main.app)


def test_list_and_connect_and_qr():
    c = _client()
    assert c.get("/api/channels").json()["whatsapp"] == "disconnected"
    assert c.post("/api/channels/whatsapp/connect").status_code == 200
    assert c.get("/api/channels").json()["whatsapp"] == "connecting"
    r = c.get("/api/channels/whatsapp/qr")
    assert r.status_code == 200 and r.content == b"FAKEPNG"
    ch.ENGINE.simulate_login("whatsapp")
    assert c.get("/api/channels/whatsapp/status").json()["status"] == "connected"
    assert c.get("/api/channels/whatsapp/qr").status_code == 404


def test_bad_channel():
    assert _client().post("/api/channels/telegram/connect").status_code == 400
