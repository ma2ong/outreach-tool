import datetime
import random
import re
import time
from typing import Callable

# per-channel: which lead column holds the contact target
_CONTACT_COL = {"whatsapp": "phone", "instagram": "instagram"}
# default rate limits (seconds) — browser channels must go slow to avoid bans
DEFAULT_DELAY = {"whatsapp": (60, 90), "instagram": (120, 240)}


def _target(channel: str, lead: dict) -> str:
    raw = lead[_CONTACT_COL[channel]]
    if channel == "whatsapp":
        return re.sub(r"\D", "", raw or "")
    return (raw or "").lstrip("@")


def eligible(conn, lead_nos: list[int], channel: str) -> list[dict]:
    if not lead_nos:
        return []
    col = _CONTACT_COL[channel]
    placeholders = ",".join("?" * len(lead_nos))
    rows = conn.execute(
        f"""SELECT l.no, l.company_en, l.phone, l.instagram FROM leads l
            WHERE l.no IN ({placeholders})
              AND l.{col} IS NOT NULL AND l.{col} != ''
              AND l.no NOT IN (
                  SELECT lead_no FROM outreach WHERE channel=? AND status='messaged')
            ORDER BY l.no""",
        [*lead_nos, channel],
    ).fetchall()
    return [dict(r) for r in rows]


def _mark_messaged(conn, lead_no: int, channel: str, date: str) -> None:
    conn.execute(
        "INSERT INTO outreach(lead_no, channel, status, touch_count, message_sent_date)"
        " VALUES (?, ?, 'messaged', 1, ?)"
        " ON CONFLICT(lead_no, channel) DO UPDATE SET"
        " status='messaged', touch_count=touch_count+1, message_sent_date=excluded.message_sent_date",
        (lead_no, channel, date),
    )
    conn.commit()


def send_channel_campaign(conn, lead_nos: list[int], channel: str, message: str,
                          engine, delay_range: tuple[int, int] | None = None,
                          on_progress: Callable[[int, int], None] | None = None) -> dict:
    if delay_range is None:
        delay_range = DEFAULT_DELAY.get(channel, (60, 90))
    today = datetime.date.today().isoformat()
    targets = eligible(conn, lead_nos, channel)
    sent = failed = 0
    errors: list[dict] = []
    for i, lead in enumerate(targets, 1):
        name = lead["company_en"]
        try:
            engine.send_message(channel, _target(channel, lead), message.format(name=name))
            _mark_messaged(conn, lead["no"], channel, today)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            errors.append({"no": lead["no"], "error": str(exc)})
        if on_progress:
            on_progress(i, len(targets))
        if i < len(targets):
            lo, hi = delay_range
            if hi > 0:
                time.sleep(random.randint(lo, hi))
    return {"sent": sent, "failed": failed,
            "skipped": len(lead_nos) - len(targets), "errors": errors}
