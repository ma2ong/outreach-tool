import pytest

import app.main as main
from app import auth
from app.db import connect, init_schema
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.execute("INSERT INTO leads(no, company_en) VALUES (1, 'Alpha')")
    c.commit()
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    monkeypatch.setattr(auth, "PASSWORD_FILE", str(tmp_path / "pw.txt"))
    monkeypatch.setattr(auth, "SESSION_KEY_FILE", str(tmp_path / ".key"))
    auth._FAILS.clear()
    return TestClient(main.app)


def _set_password(tmp_path, pw="s3cret"):
    (tmp_path / "pw.txt").write_text(pw, encoding="utf-8")


def test_no_password_file_auth_disabled(client):
    assert client.get("/api/auth/status").json() == {"enabled": False, "authed": True}
    assert client.get("/api/leads").status_code == 200


def test_api_locked_without_login(client, tmp_path):
    _set_password(tmp_path)
    assert client.get("/api/leads").status_code == 401
    assert client.get("/api/stats").status_code == 401
    # login/status stay reachable so the login page can work
    assert client.get("/api/auth/status").json() == {"enabled": True, "authed": False}


def test_wrong_password_rejected(client, tmp_path):
    _set_password(tmp_path)
    assert client.post("/api/login", json={"password": "nope"}).status_code == 401


def test_login_sets_cookie_and_unlocks(client, tmp_path):
    _set_password(tmp_path)
    r = client.post("/api/login", json={"password": "s3cret"})
    assert r.status_code == 200
    assert client.get("/api/leads").status_code == 200
    assert client.get("/api/auth/status").json()["authed"] is True


def test_logout_locks_again(client, tmp_path):
    _set_password(tmp_path)
    client.post("/api/login", json={"password": "s3cret"})
    client.post("/api/logout")
    assert client.get("/api/leads").status_code == 401


def test_lockout_after_repeated_failures(client, tmp_path):
    _set_password(tmp_path)
    for _ in range(auth.LOCKOUT_AFTER):
        client.post("/api/login", json={"password": "bad"})
    r = client.post("/api/login", json={"password": "s3cret"})
    assert r.status_code == 429


def test_forged_cookie_rejected(client, tmp_path):
    _set_password(tmp_path)
    client.cookies.set(auth.COOKIE_NAME, "f" * 64)
    assert client.get("/api/leads").status_code == 401
