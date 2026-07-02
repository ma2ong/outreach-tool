import os
import sqlite3

from app.db import connect

DB_PATH = os.environ.get("OUTREACH_DB", "outreach.db")


def get_conn() -> sqlite3.Connection:
    conn = connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
