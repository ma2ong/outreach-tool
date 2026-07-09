import app.main as main
from app.api import replies as replies_api
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, email) VALUES (1, 'Alpha', 'a@alpha.com');
        INSERT INTO outreach(lead_no, channel, status, touch_count) VALUES (1, 'email', 'messaged', 1);
    """)
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    return TestClient(main.app)


def test_poll_marks_matching_reply(tmp_path):
    client = _client(tmp_path)
    replies_api.FETCHER = lambda days: ["a@alpha.com"]
    try:
        r = client.post("/api/replies/poll")
        assert r.status_code == 200
        assert r.json()["lead_nos"] == [1]
    finally:
        replies_api.FETCHER = replies_api.replies.fetch_recent_senders
