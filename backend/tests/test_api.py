import app.main as main
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, website) VALUES
            (1,'Alpha','USA','a.com'),(2,'Beta','Brazil','b.com');
        INSERT INTO outreach(lead_no, channel, status) VALUES (1,'email','messaged');
    """)
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    return TestClient(main.app)


def test_list_leads(tmp_path):
    r = _client(tmp_path).get("/api/leads")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_leads_filter(tmp_path):
    r = _client(tmp_path).get("/api/leads?country=USA")
    assert [l["no"] for l in r.json()] == [1]


def test_get_lead(tmp_path):
    r = _client(tmp_path).get("/api/leads/1")
    assert r.status_code == 200
    assert r.json()["company_en"] == "Alpha"


def test_get_lead_404(tmp_path):
    assert _client(tmp_path).get("/api/leads/999").status_code == 404


def test_stats(tmp_path):
    r = _client(tmp_path).get("/api/stats")
    assert r.json()["total"] == 2


def test_mark_replied(tmp_path):
    client = _client(tmp_path)
    r = client.post("/api/leads/1/reply", json={"channel": "email"})
    assert r.status_code == 200
    lead = client.get("/api/leads/1").json()
    assert {"channel": "email", "status": "replied"}.items() <= {
        k: v for o in lead["outreach"] for k, v in o.items() if o["channel"] == "email"}.items()


def test_mark_replied_upserts_when_no_row(tmp_path):
    client = _client(tmp_path)
    r = client.post("/api/leads/2/reply", json={"channel": "whatsapp"})
    assert r.status_code == 200
    lead = client.get("/api/leads/2").json()
    assert any(o["channel"] == "whatsapp" and o["status"] == "replied" for o in lead["outreach"])


def test_mark_replied_bad(tmp_path):
    client = _client(tmp_path)
    assert client.post("/api/leads/999/reply", json={"channel": "email"}).status_code == 404
    assert client.post("/api/leads/1/reply", json={"channel": "telegram"}).status_code == 400
