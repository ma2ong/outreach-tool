import app.main as main
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, website, email, phone, stage) VALUES
            (1, 'Ara System', 'South Korea', 'arasystem.kr', 'i@arasystem.kr', '+827048950794', 'new'),
            (2, 'GLD LED', 'South Korea', 'gldled.com', NULL, '+8613809866355', 'new'),
            (3, 'Alibaba', 'China', 'alibaba.com', NULL, NULL, 'new');
    """)
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    return TestClient(main.app), db


def test_scan_endpoint(tmp_path):
    client, _ = _client(tmp_path)
    r = client.get("/api/health/scan").json()
    assert r["issues"]["peer"][0]["no"] == 2
    assert r["issues"]["directory"][0]["no"] == 3
    assert r["total"] >= 2


def test_fix_endpoint_suppresses(tmp_path):
    client, db = _client(tmp_path)
    r = client.post("/api/health/fix", json={"issues": ["peer", "directory"]})
    assert r.json() == {"peer": 1, "directory": 1}
    conn = connect(db)
    dnc = {x["no"] for x in conn.execute("SELECT no FROM leads WHERE do_not_contact=1")}
    assert dnc == {2, 3}
    # scanning again finds nothing to suppress
    assert "peer" not in client.get("/api/health/scan").json()["issues"]


def test_seed_loads_templates_and_sequence(tmp_path):
    client, _ = _client(tmp_path)
    r = client.post("/api/seeds/load").json()
    assert r["templates"] > 0 and r["sequence_id"] is not None
    email_tpls = client.get("/api/templates?channel=email").json()
    assert any("首次触达" in t["name"] for t in email_tpls)
    assert {t["lang"] for t in email_tpls} >= {"en", "es", "pt"}
    wa = client.get("/api/templates?channel=whatsapp").json()
    assert wa and "Shenzhen" in wa[0]["body"] and "Maxcolor" not in wa[0]["body"]  # DM 规矩：不提公司名
    seqs = client.get("/api/sequences").json()
    assert len(seqs[0]["steps"]) == 3
    assert [s["day_offset"] for s in seqs[0]["steps"]] == [0, 3, 8]


def test_seed_is_idempotent(tmp_path):
    client, _ = _client(tmp_path)
    first = client.post("/api/seeds/load").json()
    second = client.post("/api/seeds/load").json()
    assert second["templates"] == 0 and second["sequence_id"] is None
    assert len(client.get("/api/templates").json()) == first["templates"]
