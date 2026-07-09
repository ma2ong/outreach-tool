import app.main as main
from app import jobs
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    import app.api.discover as disc
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.execute("INSERT INTO leads(no, company_en, website) VALUES (1,'Alpha','alpha.com')")
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    disc.DB_PATH = db
    disc.SEARCH_FN = lambda q, limit: [{"domain": "alpha.com", "title": "Alpha"},
                                       {"domain": "newco.com", "title": "New Co"}]
    disc.ENRICH_FN = lambda d: {"domain": d, "emails": [f"info@{d}"], "email": f"info@{d}"}
    return TestClient(main.app), db


def test_discover_job_and_import(tmp_path):
    jobs.clear()
    client, db = _client(tmp_path)
    r = client.post("/api/discover", json={"query": "led wall", "limit": 10})
    jid = r.json()["job_id"]
    job = client.get(f"/api/discover/jobs/{jid}").json()
    assert job["status"] == "done"
    cands = job["result"]["candidates"]
    assert {c["domain"] for c in cands} == {"alpha.com", "newco.com"}
    # import the new one with full contact fields
    r2 = client.post("/api/leads/import", json={"country": "USA", "candidates": [
        {"company_en": "New Co", "website": "newco.com", "email": "info@newco.com",
         "phone": "+5511956635316", "instagram": "newcoig", "facebook": "newcofb",
         "linkedin": "linkedin.com/company/newco"}]})
    assert r2.json()["imported"] == 1
    conn = connect(db)
    row = conn.execute("SELECT * FROM leads WHERE website='newco.com'").fetchone()
    assert row is not None
    assert row["phone"] == "+5511956635316"
    assert row["instagram"] == "newcoig"
    assert row["facebook"] == "newcofb"
    assert row["linkedin"] == "linkedin.com/company/newco"


def test_discover_page_harvests_and_tags_source(tmp_path):
    import app.api.discover as disc
    jobs.clear()
    client, _ = _client(tmp_path)
    disc.HARVEST_FN = lambda url, limit: ["alpha.com", "distco.com"]
    r = client.post("/api/discover/page", json={"url": "https://absen.com/where-to-buy", "limit": 40})
    assert r.status_code == 200
    job = client.get(f"/api/discover/jobs/{r.json()['job_id']}").json()
    assert job["status"] == "done"
    cands = job["result"]["candidates"]
    assert {c["domain"] for c in cands} == {"alpha.com", "distco.com"}
    assert all(c["source"] == "名录/经销商页" for c in cands)


def test_discover_page_rejects_bad_url(tmp_path):
    client, _ = _client(tmp_path)
    assert client.post("/api/discover/page", json={"url": "absen.com"}).status_code == 400


def test_discover_jobs_404(tmp_path):
    client, _ = _client(tmp_path)
    assert client.get("/api/discover/jobs/nope").status_code == 404
