import app.main as main
from app import jobs
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    import app.api.verify as verify_api
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, email) VALUES
            (1, 'Good', 'john@good.com'), (2, 'Dead', 'x@dead.com');
    """)
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    verify_api.DB_PATH = db
    verify_api.RESOLVER = lambda d: d == "good.com"
    return TestClient(main.app), db


def test_verify_job_marks_statuses(tmp_path):
    jobs.clear()
    client, db = _client(tmp_path)
    r = client.post("/api/leads/verify", json={})
    jid = r.json()["job_id"]
    job = client.get(f"/api/leads/verify/jobs/{jid}").json()
    assert job["status"] == "done"
    assert job["result"] == {"checked": 2, "valid": 1, "role": 0, "invalid": 1, "unknown": 0}
    conn = connect(db)
    assert conn.execute("SELECT email_status FROM leads WHERE no=2").fetchone()["email_status"] == "invalid"


def test_verify_jobs_404(tmp_path):
    client, _ = _client(tmp_path)
    assert client.get("/api/leads/verify/jobs/nope").status_code == 404
