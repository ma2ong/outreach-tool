import app.main as main
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    db = str(tmp_path / "t.db")
    c = connect(db); init_schema(c); c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    return TestClient(main.app)


def test_template_crud(tmp_path):
    client = _client(tmp_path)
    r = client.post("/api/templates", json={"name": "WA 开场", "channel": "whatsapp", "body": "Hi {name}"})
    assert r.status_code == 200
    tid = r.json()["id"]
    assert client.get("/api/templates?channel=whatsapp").json()[0]["name"] == "WA 开场"
    assert client.get("/api/templates?channel=email").json() == []
    assert client.delete(f"/api/templates/{tid}").status_code == 200
    assert client.get("/api/templates").json() == []


def test_template_validation(tmp_path):
    client = _client(tmp_path)
    assert client.post("/api/templates", json={"name": " ", "channel": "email", "body": "x"}).status_code == 400
    assert client.delete("/api/templates/999").status_code == 404
