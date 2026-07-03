from app.browser_engine import FakeEngine


def test_fake_engine_status_and_connect():
    e = FakeEngine()
    assert e.status("whatsapp") == "disconnected"
    e.connect("whatsapp")
    assert e.status("whatsapp") == "connecting"
    e.simulate_login("whatsapp")
    assert e.status("whatsapp") == "connected"


def test_fake_engine_qr():
    e = FakeEngine()
    e.connect("whatsapp")
    assert e.qr_png("whatsapp") == b"FAKEPNG"
    e.simulate_login("whatsapp")
    assert e.qr_png("whatsapp") is None  # no QR once connected
