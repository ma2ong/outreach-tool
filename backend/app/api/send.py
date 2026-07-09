from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app import jobs, outreach, channel_outreach, mailboxes
from app.api import channels as channels_api
from app.channels import email_adapter
from app.channels.email_adapter import send_email
from app.main_deps import DB_PATH, get_conn
from app.db import connect

router = APIRouter(prefix="/api/send")

# Injectable for tests; defaults to real SMTP send.
SENDER = send_email
DELAY_RANGE = (16, 28)
DEFAULT_ATTACHMENT = r"C:\Users\Administrator\Desktop\Recent-led-projects-poster-4k.jpg"


class EmailSendRequest(BaseModel):
    lead_nos: list[int]
    subject: str
    body: str
    attachment: str | None = DEFAULT_ATTACHMENT


def _rotating_sender(conn):
    """Per-email sender that rotates configured mailboxes and records usage."""
    def send(to, subject, body, attachment):
        mbx = mailboxes.pick_mailbox(conn)
        if mbx is None:
            raise RuntimeError("no mailbox capacity")
        email_adapter.send_via(mbx, to, subject, body, attachment)
        mailboxes.record_send(conn, mbx["id"])
    return send


def _run(job_id: str, req: EmailSendRequest):
    conn = connect(DB_PATH)
    try:
        rotate = mailboxes.has_active(conn)
        sender = _rotating_sender(conn) if rotate else SENDER
        max_send = mailboxes.total_remaining(conn) if rotate else None
        result = outreach.send_campaign(
            conn, req.lead_nos, req.subject, req.body, req.attachment,
            sender=sender, delay_range=DELAY_RANGE, max_send=max_send,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, result)
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.post("/email")
def send_email_campaign(req: EmailSendRequest, background: BackgroundTasks, conn=Depends(get_conn)):
    eligible = outreach.eligible_leads(conn, req.lead_nos, "email")
    resp = {"job_id": None, "eligible": len(eligible), "selected": len(req.lead_nos)}
    if mailboxes.has_active(conn):
        resp["will_send"] = min(len(eligible), mailboxes.total_remaining(conn))
    job_id = jobs.create(total=resp.get("will_send", len(eligible)))
    resp["job_id"] = job_id
    background.add_task(_run, job_id, req)
    return resp


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


# ---- browser channels (WhatsApp / Instagram) ----
CHANNEL_DELAY = None  # None -> per-channel defaults; injectable in tests


class ChannelSendRequest(BaseModel):
    channel: str
    lead_nos: list[int]
    message: str
    image: str | None = DEFAULT_ATTACHMENT  # 规矩：DM 必须同步发案例图


def _run_channel(job_id: str, req: ChannelSendRequest):
    conn = connect(DB_PATH)
    try:
        result = channel_outreach.send_channel_campaign(
            conn, req.lead_nos, req.channel, req.message, channels_api.ENGINE,
            delay_range=CHANNEL_DELAY, image=req.image,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, result)
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.get("/quota")
def quota(conn=Depends(get_conn)):
    return {c: {"sent_today": channel_outreach.sent_today(conn, c), "cap": cap}
            for c, cap in channel_outreach.DAILY_CAP.items()}


@router.post("/channel")
def send_channel(req: ChannelSendRequest, background: BackgroundTasks, conn=Depends(get_conn)):
    if req.channel not in ("whatsapp", "instagram"):
        raise HTTPException(status_code=400, detail="unsupported channel")
    if req.image and not Path(req.image).is_file():
        raise HTTPException(status_code=400, detail=f"image not found: {req.image}")
    eligible = channel_outreach.eligible(conn, req.lead_nos, req.channel)
    remaining_today = max(0, channel_outreach.DAILY_CAP[req.channel]
                          - channel_outreach.sent_today(conn, req.channel))
    will_send = min(len(eligible), channel_outreach.MAX_BATCH, remaining_today)
    job_id = jobs.create(total=will_send)
    background.add_task(_run_channel, job_id, req)
    return {"job_id": job_id, "eligible": len(eligible), "selected": len(req.lead_nos),
            "will_send": will_send}
