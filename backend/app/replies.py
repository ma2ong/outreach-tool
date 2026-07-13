"""Inbox intelligence: poll IMAP, store reply content, handle bounces & unsubscribes.

Each fetched message is classified:
- bounce   (mailer-daemon / delivery-failure): extract the failed recipient, mark that
  lead's email_status='invalid' so every send path skips it. Not a reply.
- unsubscribe (remove me / stop ...): set lead.do_not_contact=1 (suppressed everywhere)
  and also mark replied (it IS a human answer, and must stop sequences).
- reply    : store content, mark replied via repository.mark_replied, which stops any
  active sequence enrollment so the follow-up queue never chases someone who answered.

Matched messages land in inbox_messages so the salesperson reads replies inside the
tool instead of digging through Gmail. A UNIQUE index dedupes re-polls.

The IMAP fetch is isolated behind a `fetch_messages` callable so tests inject fake
messages and never touch the network.
"""
import datetime as _dt
import email
import imaplib
import re
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime

from app import repository
from app.channels.email_adapter import GMAIL_USER, get_password

_EMAIL_RE = re.compile(r"[^@\s<>,;:\"']+@[^@\s<>,;:\"']+\.[^@\s<>,;:\"']+")
_BOUNCE_FROM_RE = re.compile(r"mailer-daemon|postmaster|mail delivery", re.I)
_BOUNCE_SUBJ_RE = re.compile(
    r"undeliver|delivery status|delivery has failed|returned to sender|failure notice|"
    r"delivery incomplete|address not found", re.I)
_UNSUB_RE = re.compile(
    r"unsubscribe|remove me|take me off|stop (contacting|emailing|sending|messaging)|"
    r"do( not|n'?t) (contact|email)", re.I)

_BODY_LIMIT = 4000


def _norm(addr: str) -> str:
    return (addr or "").strip().lower()


def _decode(value) -> str:
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:  # noqa: BLE001
        return value or ""


def _plain_body(msg) -> str:
    parts = msg.walk() if msg.is_multipart() else [msg]
    fallback = ""
    for part in parts:
        if part.get_content_maintype() != "text":
            continue
        try:
            text = part.get_payload(decode=True).decode(
                part.get_content_charset() or "utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if part.get_content_subtype() == "plain":
            return text[:_BODY_LIMIT]
        fallback = fallback or re.sub(r"<[^>]+>", " ", text)
    return fallback[:_BODY_LIMIT]


def fetch_recent_messages(since_days: int = 7) -> list[dict]:
    """Real IMAP: full messages (sender/subject/body/date) from the last `since_days`."""
    pw = get_password()
    if not pw:
        raise RuntimeError("Gmail app password missing (~/.gmail_app_password or GMAIL_APP_PASSWORD)")
    since = (_dt.date.today() - _dt.timedelta(days=since_days)).strftime("%d-%b-%Y")
    messages: list[dict] = []
    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as im:
        im.login(GMAIL_USER, pw)
        im.select("INBOX")
        typ, data = im.search(None, f'(SINCE "{since}")')
        if typ != "OK":
            return []
        for num in data[0].split():
            typ, msg_data = im.fetch(num, "(BODY.PEEK[])")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            _, addr = parseaddr(msg.get("From", ""))
            try:
                received = parsedate_to_datetime(msg.get("Date")).isoformat()
            except Exception:  # noqa: BLE001
                received = ""
            messages.append({
                "from_addr": _norm(addr),
                "subject": _decode(msg.get("Subject", "")),
                "body": _plain_body(msg),
                "received_at": received,
            })
    return messages


def _store(conn, lead_no: int, kind: str, m: dict) -> bool:
    cur = conn.execute(
        "INSERT OR IGNORE INTO inbox_messages(lead_no, channel, kind, from_addr, subject, body, received_at)"
        " VALUES (?, 'email', ?, ?, ?, ?, ?)",
        (lead_no, kind, _norm(m.get("from_addr")), m.get("subject") or "",
         m.get("body") or "", m.get("received_at") or ""))
    return cur.rowcount > 0


def _lead_emails(conn) -> dict[str, int]:
    rows = conn.execute(
        "SELECT no, email FROM leads WHERE email IS NOT NULL AND email != ''").fetchall()
    return {_norm(r["email"]): r["no"] for r in rows}


def process_messages(conn, messages: list[dict]) -> dict:
    """Classify and store fetched messages against the lead base."""
    by_email = _lead_emails(conn)
    replies_n = bounces = unsubs = stored = 0
    lead_nos: list[int] = []
    for m in messages:
        sender = _norm(m.get("from_addr"))
        subject, body = m.get("subject") or "", m.get("body") or ""
        if _BOUNCE_FROM_RE.search(sender) or _BOUNCE_SUBJ_RE.search(subject):
            failed = [a for a in _EMAIL_RE.findall(body) if _norm(a) in by_email]
            for addr in {_norm(a) for a in failed}:
                no = by_email[addr]
                conn.execute("UPDATE leads SET email_status='invalid' WHERE no=?", (no,))
                if _store(conn, no, "bounce", m):
                    stored += 1
                bounces += 1
                lead_nos.append(no)
            continue
        no = by_email.get(sender)
        if no is None:
            continue
        kind = "unsubscribe" if _UNSUB_RE.search(subject) or _UNSUB_RE.search(body) else "reply"
        if _store(conn, no, kind, m):
            stored += 1
        if kind == "unsubscribe":
            conn.execute("UPDATE leads SET do_not_contact=1 WHERE no=?", (no,))
            unsubs += 1
        else:
            replies_n += 1
        repository.mark_replied(conn, no, "email")
        lead_nos.append(no)
    conn.commit()
    return {"replies": replies_n, "bounces": bounces, "unsubscribes": unsubs,
            "stored": stored, "lead_nos": lead_nos}


def match_and_mark(conn, sender_emails: list[str]) -> dict:
    """Mark leads whose email matches a sender as replied on the email channel.
    Returns {matched, newly_replied, lead_nos}."""
    wanted = {_norm(a) for a in sender_emails if a}
    if not wanted:
        return {"matched": 0, "newly_replied": 0, "lead_nos": []}
    by_email = _lead_emails(conn)
    newly, lead_nos = 0, []
    for addr, no in by_email.items():
        if addr not in wanted:
            continue
        lead_nos.append(no)
        already = conn.execute(
            "SELECT 1 FROM outreach WHERE lead_no=? AND channel='email' AND status='replied'",
            (no,)).fetchone()
        repository.mark_replied(conn, no, "email")
        if not already:
            newly += 1
    return {"matched": len(lead_nos), "newly_replied": newly, "lead_nos": lead_nos}


def poll_replies(conn, fetch_messages=fetch_recent_messages, since_days: int = 7) -> dict:
    return process_messages(conn, fetch_messages(since_days))
