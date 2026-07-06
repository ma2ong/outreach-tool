import app.main as main
import app.api.send as send_api
import app.api.channels as channels_api
from app import jobs
from app.browser_engine import FakeEngine
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, phone, instagram) VALUES
            (1,'Alpha','+1 555 111 2222','alpha_ig'),
            (2,'Beta',NULL,'beta_ig');
    """)
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    send_api.DB_PATH = db
    send_api.CHANNEL_DELAY = (0, 0)
    channels_api.ENGINE = FakeEngine()
    return TestClient(main.app), db


def test_send_whatsapp_channel(tmp_path):
    jobs.clear()
    client, db = _client(tmp_path)
    r = client.post("/api/send/channel", json={"channel": "whatsapp", "lead_nos": [1, 2], "message": "Hi {name}", "image": None})
    assert r.status_code == 200
    assert r.json()["eligible"] == 1  # only lead 1 has a phone
    jid = r.json()["job_id"]
    job = client.get(f"/api/send/jobs/{jid}").json()
    assert job["status"] == "done"
    assert job["result"]["sent"] == 1
    assert channels_api.ENGINE.sent == [("whatsapp", "15551112222", "Hi Alpha", None)]


def test_send_channel_missing_image_rejected(tmp_path):
    client, _ = _client(tmp_path)
    r = client.post("/api/send/channel", json={
        "channel": "whatsapp", "lead_nos": [1], "message": "x",
        "image": "C:/no/such/file.jpg"})
    assert r.status_code == 400
    assert "image" in r.json()["detail"]


def test_send_channel_bad(tmp_path):
    client, _ = _client(tmp_path)
    assert client.post("/api/send/channel", json={"channel": "telegram", "lead_nos": [1], "message": "x"}).status_code == 400
