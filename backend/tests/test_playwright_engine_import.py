def test_playwright_engine_instantiates_without_launching():
    from app.playwright_engine import PlaywrightEngine
    e = PlaywrightEngine()  # must NOT launch a browser on construction
    assert e.status("whatsapp") == "disconnected"
    assert e.qr_png("whatsapp") is None
