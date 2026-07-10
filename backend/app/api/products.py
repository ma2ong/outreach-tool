import datetime as dt
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import quote
from app.main_deps import DB_PATH as _DB_PATH, get_conn

router = APIRouter(prefix="/api")

DB_PATH = _DB_PATH


def _quotes_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(DB_PATH)), "quotes")


class ProductCreate(BaseModel):
    model: str
    pixel_pitch: str | None = None
    brightness: str | None = None
    use_case: str | None = None
    ref_price_sqm: str | None = None


class QuoteRequest(BaseModel):
    product_ids: list[int]
    note: str = ""


@router.get("/products")
def list_products(conn=Depends(get_conn)):
    return [dict(r) for r in conn.execute("SELECT * FROM products ORDER BY id")]


@router.post("/products")
def create_product(req: ProductCreate, conn=Depends(get_conn)):
    if not req.model.strip():
        raise HTTPException(status_code=400, detail="model required")
    cur = conn.execute(
        "INSERT INTO products(model, pixel_pitch, brightness, use_case, ref_price_sqm)"
        " VALUES (?, ?, ?, ?, ?)",
        (req.model.strip(), req.pixel_pitch, req.brightness, req.use_case, req.ref_price_sqm))
    conn.commit()
    return dict(conn.execute("SELECT * FROM products WHERE id=?", (cur.lastrowid,)).fetchone())


@router.post("/products/seed")
def seed_products(conn=Depends(get_conn)):
    """Load the default Maxcolor range (only when the table is empty)."""
    if conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
        raise HTTPException(status_code=400, detail="products already exist")
    for p in quote.DEFAULT_PRODUCTS:
        conn.execute(
            "INSERT INTO products(model, pixel_pitch, brightness, use_case, ref_price_sqm)"
            " VALUES (?, ?, ?, ?, ?)",
            (p["model"], p["pixel_pitch"], p["brightness"], p["use_case"], p["ref_price_sqm"]))
    conn.commit()
    return {"seeded": len(quote.DEFAULT_PRODUCTS)}


@router.delete("/products/{pid}")
def delete_product(pid: int, conn=Depends(get_conn)):
    cur = conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="product not found")
    return {"ok": True}


@router.post("/quote")
def generate_quote(req: QuoteRequest, conn=Depends(get_conn)):
    if not req.product_ids:
        raise HTTPException(status_code=400, detail="pick at least one product")
    ph = ",".join("?" * len(req.product_ids))
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM products WHERE id IN ({ph}) ORDER BY id", req.product_ids)]
    if not rows:
        raise HTTPException(status_code=404, detail="products not found")
    name = f"quote_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = quote.render_quote(rows, os.path.join(_quotes_dir(), name), note=req.note.strip())
    return {"file": name, "path": os.path.abspath(path)}


@router.get("/quote/file/{name}")
def quote_file(name: str):
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="bad name")
    path = os.path.join(_quotes_dir(), name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path, media_type="image/png")
