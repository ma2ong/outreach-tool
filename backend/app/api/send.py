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
    campaign: str | None = None


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
        sender = _rotating_sender(conn) if mailboxes.has_active(conn) else SENDER
        result = outreach.send_campaign(
            conn, req.lead_nos, req.subject, req.body, req.attachment,
            sender=sender, delay_range=DELAY_RANGE,
            campaign=req.campaign,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, result)
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.post("/email")
def send_email_campaign(req: EmailSendRequest, background: BackgroundTasks, conn=Depends(get_conn)):
    eligible = outreach.eligible_leads(conn, req.lead_nos, "email")
    will_send = min(len(eligible), outreach.remaining_today(conn), outreach.MAX_BATCH)
    job_id = jobs.create(total=will_send)
    background.add_task(_run, job_id, req)
    return {"job_id": job_id, "eligible": len(eligible), "selected": len(req.lead_nos),
            "will_send": will_send}


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
    campaign: str | None = None


def _run_channel(job_id: str, req: ChannelSendRequest):
    conn = connect(DB_PATH)
    try:
        result = channel_outreach.send_channel_campaign(
            conn, req.lead_nos, req.channel, req.message, channels_api.ENGINE,
            delay_range=CHANNEL_DELAY, image=req.image, campaign=req.campaign,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, result)
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.get("/quota")
def quota(conn=Depends(get_conn)):
    q = {c: {"sent_today": channel_outreach.sent_today(conn, c), "cap": cap}
         for c, cap in channel_outreach.DAILY_CAP.items()}
    email_sent = outreach.sent_today(conn)
    q["email"] = {"sent_today": email_sent,
                  "cap": email_sent + outreach.remaining_today(conn),
                  "batch": outreach.MAX_BATCH,
                  "mailboxes": mailboxes.has_active(conn)}
    return q


@router.post("/channel")
def send_channel(req: ChannelSendRequest, background: BackgroundTasks, conn=Depends(get_conn)):
    if req.channel not in ("whatsapp", "instagram", "facebook"):
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
