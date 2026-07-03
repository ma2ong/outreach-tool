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
    # import the new one
    r2 = client.post("/api/leads/import", json={"country": "USA", "candidates": [
        {"company_en": "New Co", "website": "newco.com", "email": "info@newco.com"}]})
    assert r2.json()["imported"] == 1
    conn = connect(db)
    assert conn.execute("SELECT COUNT(*) c FROM leads WHERE website='newco.com'").fetchone()["c"] == 1


def test_discover_jobs_404(tmp_path):
    client, _ = _client(tmp_path)
    assert client.get("/api/discover/jobs/nope").status_code == 404
