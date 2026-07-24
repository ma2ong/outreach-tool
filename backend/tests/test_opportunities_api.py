import app.main as main
from app.db import connect, init_schema
from app import opportunities
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    conn = connect(db)
    init_schema(conn)
    opportunities.ensure_schema(conn)
    conn.execute(
        "INSERT INTO leads(no, company_en, country) VALUES (1,'Alpha AV','USA')")
    conn.commit()
    conn.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    return TestClient(main.app)


def test_opportunity_crud_and_stats(tmp_path):
    client = _client(tmp_path)
    created = client.post("/api/opportunities", json={
        "lead_no": 1,
        "title": "Lobby P1.8",
        "amount": 30000,
        "next_action": "确认 CAD",
        "next_action_date": "2026-07-20",
    })
    assert created.status_code == 200
    oid = created.json()["id"]
    assert client.get("/api/opportunities?lead_no=1").json()[0]["id"] == oid

    moved = client.patch(f"/api/opportunities/{oid}", json={
        "stage": "quoted",
        "amount": 32000,
        "next_action": "催采购确认",
    })
    assert moved.status_code == 200
    assert moved.json()["stage"] == "quoted"
    stats = client.get("/api/opportunities/stats").json()
    assert stats["open_count"] == 1
    assert stats["weighted_amount"] == 19200


def test_stage_validation_is_actionable(tmp_path):
    client = _client(tmp_path)
    oid = client.post("/api/opportunities", json={
        "lead_no": 1, "title": "Stage project"}).json()["id"]
    response = client.patch(f"/api/opportunities/{oid}", json={"stage": "lost"})
    assert response.status_code == 400
    assert "丢单原因" in response.json()["detail"]


def test_unknown_lead_and_opportunity(tmp_path):
    client = _client(tmp_path)
    assert client.post("/api/opportunities", json={
        "lead_no": 999, "title": "No buyer"}).status_code == 400
    assert client.patch("/api/opportunities/999", json={"title": "x"}).status_code == 404

