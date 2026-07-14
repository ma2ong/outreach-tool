"""Lead-base health check: find data that is quietly costing money, then fix it.

Every issue here wastes something real — sending budget on peers, daily WhatsApp
quota on leads with no phone, or a stage board that lies about where deals stand.
Fixes are conservative: peers/directories are suppressed (do_not_contact), never
deleted, so a wrong call is one click to undo.
"""
from app import screening

ISSUES = ("peer", "directory", "no_contact", "junk_name", "stale_stage")

_JUNK_NAMES = ("contact", "contact us", "contact-us", "home", "about", "index",
               "page not found", "404")


def _rows(conn):
    return conn.execute(
        "SELECT no, company_en, country, website, email, phone, instagram, facebook, stage,"
        "       COALESCE(do_not_contact, 0) dnc FROM leads").fetchall()


def _is_junk_name(name: str | None) -> bool:
    n = (name or "").strip().lower()
    return len(n) < 3 or n in _JUNK_NAMES


def scan(conn) -> dict:
    """Group the lead base's problems, each with the leads it affects."""
    found: dict[str, list[dict]] = {k: [] for k in ISSUES}
    messaged = {r["lead_no"] for r in conn.execute(
        "SELECT DISTINCT lead_no FROM outreach WHERE status IN ('messaged','replied')")}
    for r in _rows(conn):
        lead = {"no": r["no"], "company_en": r["company_en"],
                "website": r["website"], "country": r["country"]}
        if not r["dnc"]:
            s = screening.screen({"domain": r["website"], "phone": r["phone"], "email": r["email"]})
            if s["excluded"]:
                key = "directory" if "目录" in (s["exclude_reason"] or "") else "peer"
                found[key].append(lead | {"reason": s["exclude_reason"]})
                continue
        if not any((r["email"], r["phone"], r["instagram"], r["facebook"])):
            found["no_contact"].append(lead)
        if _is_junk_name(r["company_en"]):
            found["junk_name"].append(lead)
        # Stage says "new" but we already messaged them — the board is lying.
        if r["no"] in messaged and (r["stage"] or "new") == "new":
            found["stale_stage"].append(lead)
    return {k: v for k, v in found.items() if v}


def fix(conn, issues: list[str]) -> dict:
    """Apply the safe fix for each requested issue. Returns what changed."""
    from app import repository
    found = scan(conn)
    done: dict[str, int] = {}
    for key in issues:
        leads = found.get(key, [])
        if key in ("peer", "directory"):
            for lead in leads:
                conn.execute("UPDATE leads SET do_not_contact=1 WHERE no=?", (lead["no"],))
                repository.add_note(conn, lead["no"],
                                    f"体检自动标记不再联系：{lead.get('reason', '同行/目录站')}")
            done[key] = len(leads)
        elif key == "stale_stage":
            for lead in leads:
                conn.execute("UPDATE leads SET stage='contacted' WHERE no=? AND stage='new'",
                             (lead["no"],))
            done[key] = len(leads)
        # no_contact / junk_name are reported only: deleting or renaming a lead is
        # Allen's call, not the tool's.
    conn.commit()
    return done
