import os

import app.main as main
from app.db import connect, init_schema
from fastapi.testclient import TestClient


def _client(tmp_path):
    import app.api.products as products_api
    db = str(tmp_path / "t.db")
    c = connect(db)
    init_schema(c)
    c.close()
    main.app.dependency_overrides[main.get_conn] = lambda: connect(db)
    products_api.DB_PATH = db  # quotes dir lands under tmp_path
    return TestClient(main.app)


def test_product_crud_and_seed(tmp_path):
    client = _client(tmp_path)
    assert client.get("/api/products").json() == []
    r = client.post("/api/products/seed")
    assert r.json()["seeded"] == 5
    assert client.post("/api/products/seed").status_code == 400  # only when empty
    prods = client.get("/api/products").json()
    assert len(prods) == 5
    r = client.post("/api/products", json={"model": "Custom P1.9", "pixel_pitch": "P1.9",
                                           "ref_price_sqm": "USD 1500"})
    pid = r.json()["id"]
    assert client.delete(f"/api/products/{pid}").status_code == 200
    assert client.delete("/api/products/999").status_code == 404
    assert client.post("/api/products", json={"model": "  "}).status_code == 400


def test_quote_renders_png(tmp_path):
    client = _client(tmp_path)
    client.post("/api/products/seed")
    ids = [p["id"] for p in client.get("/api/products").json()[:3]]
    r = client.post("/api/quote", json={"product_ids": ids, "note": "MOQ 10 sqm"})
    assert r.status_code == 200
    path = r.json()["path"]
    assert os.path.isfile(path) and os.path.getsize(path) > 5000
    with open(path, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"
    # preview endpoint serves it
    img = client.get(f"/api/quote/file/{r.json()['file']}")
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"


def test_quote_validation(tmp_path):
    client = _client(tmp_path)
    assert client.post("/api/quote", json={"product_ids": []}).status_code == 400
    assert client.post("/api/quote", json={"product_ids": [999]}).status_code == 404
    assert client.get("/api/quote/file/..%2Fx.png").status_code in (400, 404)
