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


def _fake_fetcher(days):
    return [{"from_addr": "a@alpha.com", "subject": "Re: LED wall",
             "body": "Send me a quote for P2.5", "received_at": "2026-07-13T08:00:00"}]


def test_poll_marks_matching_reply(tmp_path):
    client = _client(tmp_path)
    replies_api.FETCHER = _fake_fetcher
    try:
        r = client.post("/api/replies/poll")
        assert r.status_code == 200
        assert r.json()["lead_nos"] == [1]
    finally:
        replies_api.FETCHER = replies_api.replies.fetch_recent_messages


def test_poll_then_inbox_lists_message(tmp_path):
    client = _client(tmp_path)
    replies_api.FETCHER = _fake_fetcher
    try:
        client.post("/api/replies/poll")
        r = client.get("/api/inbox")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        m = items[0]
        assert m["company_en"] == "Alpha" and m["kind"] == "reply"
        assert "P2.5" in m["body"] and m["is_read"] == 0
        # unread badge count
        assert client.get("/api/inbox/unread_count").json()["count"] == 1
        # mark read
        assert client.post(f"/api/inbox/{m['id']}/read").status_code == 200
        assert client.get("/api/inbox/unread_count").json()["count"] == 0
    finally:
        replies_api.FETCHER = replies_api.replies.fetch_recent_messages


def test_inbox_unread_only_filter(tmp_path):
    client = _client(tmp_path)
    replies_api.FETCHER = _fake_fetcher
    try:
        client.post("/api/replies/poll")
        m = client.get("/api/inbox").json()[0]
        client.post(f"/api/inbox/{m['id']}/read")
        assert client.get("/api/inbox?unread_only=1").json() == []
        assert len(client.get("/api/inbox").json()) == 1
    finally:
        replies_api.FETCHER = replies_api.replies.fetch_recent_messages
