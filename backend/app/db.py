import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    no INTEGER PRIMARY KEY,
    company_en TEXT NOT NULL,
    company_local TEXT,
    country TEXT,
    region TEXT,
    city TEXT,
    contact_name TEXT,
    title TEXT,
    email TEXT,
    phone TEXT,
    website TEXT,
    instagram TEXT,
    facebook TEXT,
    linkedin TEXT,
    business TEXT,
    target_fit TEXT,
    whatsapp_verified INTEGER DEFAULT 0,
    source_urls TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_no INTEGER NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    touch_count INTEGER DEFAULT 0,
    message_sent_date TEXT,
    reply_received INTEGER DEFAULT 0,
    exclude_reason TEXT,
    UNIQUE(lead_no, channel)
);
CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);
CREATE INDEX IF NOT EXISTS idx_outreach_channel ON outreach(channel, status);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
