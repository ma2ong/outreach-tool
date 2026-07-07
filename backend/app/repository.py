import json
import sqlite3

from app.models import Lead, OutreachStatus, Stats


def _lead_from_row(row: sqlite3.Row, outreach: list[OutreachStatus]) -> Lead:
    d = dict(row)
    d["whatsapp_verified"] = bool(d.get("whatsapp_verified"))
    raw = d.get("source_urls")
    d["source_urls"] = json.loads(raw) if raw else []
    fields = {k: d.get(k) for k in Lead.model_fields if k != "outreach"}
    return Lead(**fields, outreach=outreach)


def _outreach_for(conn: sqlite3.Connection, lead_nos: list[int]) -> dict[int, list[OutreachStatus]]:
    if not lead_nos:
        return {}
    q = "SELECT * FROM outreach WHERE lead_no IN (%s)" % ",".join("?" * len(lead_nos))
    out: dict[int, list[OutreachStatus]] = {}
    for r in conn.execute(q, lead_nos):
        out.setdefault(r["lead_no"], []).append(OutreachStatus(
            channel=r["channel"], status=r["status"], touch_count=r["touch_count"] or 0,
            message_sent_date=r["message_sent_date"], reply_received=bool(r["reply_received"]),
            exclude_reason=r["exclude_reason"],
        ))
    return out


_HAS_COLS = {"phone": "phone", "instagram": "instagram", "email": "email"}
_TOUCHED = "status IN ('messaged','replied')"


def list_leads(conn, country=None, channel=None, status=None, search=None, has=None) -> list[Lead]:
    where, params = [], []
    if country:
        where.append("l.country = ?")
        params.append(country)
    if search:
        where.append("(l.company_en LIKE ? OR l.website LIKE ? OR l.city LIKE ?)")
        params += [f"%{search}%"] * 3
    if has:
        col = _HAS_COLS.get(has)
        if col:
            where.append(f"l.{col} IS NOT NULL AND l.{col} != ''")
    if status == "untouched":
        if channel:
            where.append("l.no NOT IN (SELECT lead_no FROM outreach"
                         f" WHERE channel = ? AND {_TOUCHED})")
            params.append(channel)
        else:
            where.append(f"l.no NOT IN (SELECT lead_no FROM outreach WHERE {_TOUCHED})")
        channel = status = None
    if channel or status:
        sub, sp = [], []
        if channel:
            sub.append("channel = ?")
            sp.append(channel)
        if status:
            sub.append("status = ?")
            sp.append(status)
        where.append("l.no IN (SELECT lead_no FROM outreach WHERE %s)" % " AND ".join(sub))
        params += sp
    sql = "SELECT l.* FROM leads l"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY l.no"
    rows = list(conn.execute(sql, params))
    om = _outreach_for(conn, [r["no"] for r in rows])
    return [_lead_from_row(r, om.get(r["no"], [])) for r in rows]


def mark_replied(conn, no: int, channel: str) -> None:
    conn.execute(
        "INSERT INTO outreach(lead_no, channel, status) VALUES (?, ?, 'replied')"
        " ON CONFLICT(lead_no, channel) DO UPDATE SET status='replied'",
        (no, channel),
    )
    conn.commit()


def get_lead(conn, no: int) -> Lead | None:
    row = conn.execute("SELECT * FROM leads WHERE no = ?", (no,)).fetchone()
    if row is None:
        return None
    om = _outreach_for(conn, [no])
    return _lead_from_row(row, om.get(no, []))


def find_duplicate(conn, website=None, instagram=None, company_en=None) -> int | None:
    checks = []
    if website:
        checks.append(("website", website))
    if instagram:
        checks.append(("instagram", instagram))
    if company_en:
        checks.append(("company_en", company_en))
    for col, val in checks:
        row = conn.execute(f"SELECT no FROM leads WHERE lower({col}) = lower(?)", (val,)).fetchone()
        if row:
            return row["no"]
    return None


def stats(conn) -> Stats:
    total = conn.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
    by_country = {r["country"]: r["c"] for r in conn.execute(
        "SELECT country, COUNT(*) c FROM leads WHERE country IS NOT NULL GROUP BY country"
    )}
    by_cs: dict[str, dict[str, int]] = {}
    for r in conn.execute(
        "SELECT channel, status, COUNT(*) c FROM outreach GROUP BY channel, status"
    ):
        by_cs.setdefault(r["channel"], {})[r["status"]] = r["c"]
    return Stats(total=total, by_country=by_country, by_channel_status=by_cs)


import datetime as _dt

_INSERT_COLS = ["company_en", "company_local", "country", "region", "city",
                "email", "phone", "website", "instagram", "facebook", "linkedin",
                "business", "target_fit"]


def next_no(conn) -> int:
    row = conn.execute("SELECT MAX(no) m FROM leads").fetchone()
    return (row["m"] or 0) + 1


def insert_lead(conn, data: dict) -> int:
    no = next_no(conn)
    cols = ["no"] + _INSERT_COLS + ["created_at", "updated_at"]
    now = _dt.datetime.now(_dt.UTC).isoformat()
    vals = [no] + [data.get(c) for c in _INSERT_COLS] + [now, now]
    placeholders = ",".join("?" * len(cols))
    conn.execute(f"INSERT INTO leads({','.join(cols)}) VALUES ({placeholders})", vals)
    conn.commit()
    return no
