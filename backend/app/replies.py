"""Email reply detection: poll the inbox, match senders to leads, mark replied.

A detected reply flows through repository.mark_replied, which flips the lead's
email outreach to 'replied' (excluding it from future blasts) and stops any active
sequence enrollment so the follow-up queue never chases someone who answered.

The IMAP fetch is isolated behind a `fetch_senders` callable so tests inject a fake
list of addresses and never touch the network.
"""
import datetime as _dt
import email
import imaplib
import re
from email.utils import parseaddr

from app import repository
from app.channels.email_adapter import GMAIL_USER, get_password

_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _norm(addr: str) -> str:
    return (addr or "").strip().lower()


def fetch_recent_senders(since_days: int = 7) -> list[str]:
    """Real IMAP: return lowercased sender addresses from the last `since_days`."""
    pw = get_password()
    if not pw:
        raise RuntimeError("Gmail app password missing (~/.gmail_app_password or GMAIL_APP_PASSWORD)")
    since = (_dt.date.today() - _dt.timedelta(days=since_days)).strftime("%d-%b-%Y")
    senders: list[str] = []
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as im:
        im.login(GMAIL_USER, pw)
        im.select("INBOX")
        typ, data = im.search(None, f'(SINCE "{since}")')
        if typ != "OK":
            return []
        for num in data[0].split():
            typ, msg_data = im.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            hdr = email.message_from_bytes(msg_data[0][1])
            _, addr = parseaddr(hdr.get("From", ""))
            if addr:
                senders.append(_norm(addr))
    return senders


def match_and_mark(conn, sender_emails: list[str]) -> dict:
    """Mark leads whose email matches a sender as replied on the email channel.
    Returns {matched, newly_replied, lead_nos}."""
    wanted = {_norm(a) for a in sender_emails if a}
    if not wanted:
        return {"matched": 0, "newly_replied": 0, "lead_nos": []}
    rows = conn.execute(
        "SELECT no, email FROM leads WHERE email IS NOT NULL AND email != ''").fetchall()
    newly, lead_nos = 0, []
    for r in rows:
        if _norm(r["email"]) not in wanted:
            continue
        lead_nos.append(r["no"])
        already = conn.execute(
            "SELECT 1 FROM outreach WHERE lead_no=? AND channel='email' AND status='replied'",
            (r["no"],)).fetchone()
        repository.mark_replied(conn, r["no"], "email")
        if not already:
            newly += 1
    return {"matched": len(lead_nos), "newly_replied": newly, "lead_nos": lead_nos}


def poll_replies(conn, fetch_senders=fetch_recent_senders, since_days: int = 7) -> dict:
    senders = fetch_senders(since_days)
    return match_and_mark(conn, senders)
