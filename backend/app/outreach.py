import datetime
import random
import time
from typing import Callable


def eligible_leads(conn, lead_nos: list[int], channel: str) -> list[dict]:
    if not lead_nos:
        return []
    placeholders = ",".join("?" * len(lead_nos))
    rows = conn.execute(
        f"""SELECT l.no, l.company_en, l.email FROM leads l
            WHERE l.no IN ({placeholders})
              AND l.email IS NOT NULL AND l.email != ''
              AND (l.email_status IS NULL OR l.email_status != 'invalid')
              AND l.no NOT IN (
                  SELECT lead_no FROM outreach WHERE channel=? AND status IN ('messaged','replied'))
            ORDER BY l.no""",
        [*lead_nos, channel],
    ).fetchall()
    return [dict(r) for r in rows]


def _mark_messaged(conn, lead_no: int, date: str) -> None:
    conn.execute(
        "INSERT INTO outreach(lead_no, channel, status, touch_count, message_sent_date)"
        " VALUES (?, 'email', 'messaged', 1, ?)"
        " ON CONFLICT(lead_no, channel) DO UPDATE SET"
        " status='messaged', touch_count=touch_count+1, message_sent_date=excluded.message_sent_date",
        (lead_no, date),
    )
    conn.commit()


def send_campaign(conn, lead_nos: list[int], subject: str, body: str,
                  attachment: str | None, sender: Callable[[str, str, str, str | None], None],
                  delay_range: tuple[int, int] = (16, 28), max_send: int | None = None,
                  on_progress: Callable[[int, int], None] | None = None) -> dict:
    today = datetime.date.today().isoformat()
    all_targets = eligible_leads(conn, lead_nos, "email")
    total_selected = len(lead_nos)
    # max_send caps a run to the sender mailboxes' remaining daily capacity (rotation).
    targets = all_targets if max_send is None else all_targets[:max_send]
    deferred = len(all_targets) - len(targets)
    sent = failed = 0
    errors: list[dict] = []
    for i, lead in enumerate(targets, 1):
        name = lead["company_en"]
        try:
            sender(lead["email"], subject.format(name=name), body.format(name=name), attachment)
            _mark_messaged(conn, lead["no"], today)
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
    return {"sent": sent, "failed": failed, "deferred": deferred,
            "skipped": total_selected - len(all_targets), "errors": errors}
