"""Send the due step of sequence enrollments, then advance them.

Unlike the one-off blast paths, this deliberately reaches leads that were already
messaged (that is the whole point of a follow-up step), so it does NOT use the
'messaged' exclusion. It still honours the browser-channel rate limits and daily
caps, and each item carries its own step message. After a successful send the
enrollment advances to its next step (or completes).
"""
import datetime
import random
import time

from app import channel_outreach as co
from app import outreach as email_outreach
from app import sequences


def _contact(conn, lead_no: int) -> dict:
    r = conn.execute("SELECT no, company_en, email, phone, instagram FROM leads WHERE no=?",
                     (lead_no,)).fetchone()
    return dict(r) if r else {}


def send_due(conn, enrollment_ids, *, sender=None, engine=None,
             email_delay=(16, 28), channel_delay=None, image_default=None,
             on_progress=None) -> dict:
    """Send the current step for the given enrollments (must be in today's due queue)."""
    due = {d["enrollment_id"]: d for d in sequences.due_queue(conn)}
    items = [due[i] for i in enrollment_ids if i in due]
    today = datetime.date.today().isoformat()
    sent = failed = deferred = 0
    errors: list[dict] = []

    # Browser channels are capped per day and per batch; email is uncapped.
    remaining = {ch: max(0, co.DAILY_CAP[ch] - co.sent_today(conn, ch)) for ch in co.DAILY_CAP}
    batch_used = {ch: 0 for ch in co.DAILY_CAP}

    total = len(items)
    for idx, d in enumerate(items, 1):
        ch, no = d["channel"], d["lead_no"]
        lead = _contact(conn, no)
        name = lead.get("company_en", "")
        try:
            if ch == "email":
                to = lead.get("email")
                if not to:
                    deferred += 1
                    continue
                sender(to, (d.get("subject") or "").format(name=name),
                       d["body"].format(name=name), d.get("image") or image_default)
                email_outreach._mark_messaged(conn, no, today)
            else:
                if remaining.get(ch, 0) <= 0 or batch_used.get(ch, 0) >= co.MAX_BATCH:
                    deferred += 1
                    continue
                target = co._target(ch, lead)
                if not target:
                    deferred += 1
                    continue
                engine.send_message(ch, target, d["body"].format(name=name),
                                    d.get("image") or image_default)
                co._mark_messaged(conn, no, ch, today)
                remaining[ch] -= 1
                batch_used[ch] += 1
            sequences.advance_enrollment(conn, d["enrollment_id"])
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            errors.append({"no": no, "error": str(exc)})
        if on_progress:
            on_progress(idx, total)
        if idx < total:
            lo, hi = channel_delay or (co.DEFAULT_DELAY.get(ch, (0, 0)) if ch != "email" else email_delay)
            if hi > 0:
                time.sleep(random.randint(lo, hi))
    return {"sent": sent, "failed": failed, "deferred": deferred, "errors": errors}
