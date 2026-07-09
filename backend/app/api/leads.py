from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import repository as repo
from app.main_deps import get_conn
from app.models import Lead

router = APIRouter(prefix="/api")

REPLY_CHANNELS = ("email", "whatsapp", "instagram")


class ReplyRequest(BaseModel):
    channel: str


class LeadUpdate(BaseModel):
    company_en: str | None = None
    company_local: str | None = None
    country: str | None = None
    city: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    business: str | None = None
    stage: str | None = None
    tags: str | None = None
    follow_up_date: str | None = None
    next_action: str | None = None


class NoteRequest(BaseModel):
    text: str


@router.get("/leads", response_model=list[Lead])
def list_leads(country: str | None = None, channel: str | None = None,
               status: str | None = None, search: str | None = None,
               has: str | None = None, conn=Depends(get_conn)):
    return repo.list_leads(conn, country=country, channel=channel, status=status,
                           search=search, has=has)


@router.get("/leads/{no}", response_model=Lead)
def get_lead(no: int, conn=Depends(get_conn)):
    lead = repo.get_lead(conn, no)
    if lead is None:
        raise HTTPException(status_code=404, detail="lead not found")
    return lead


@router.patch("/leads/{no}", response_model=Lead)
def update_lead(no: int, req: LeadUpdate, conn=Depends(get_conn)):
    fields = req.model_dump(exclude_unset=True)
    if not repo.update_lead(conn, no, fields):
        raise HTTPException(status_code=404, detail="lead not found")
    return repo.get_lead(conn, no)


@router.get("/leads/{no}/notes")
def list_notes(no: int, conn=Depends(get_conn)):
    if repo.get_lead(conn, no) is None:
        raise HTTPException(status_code=404, detail="lead not found")
    return repo.list_notes(conn, no)


@router.post("/leads/{no}/notes", response_model=Lead)
def add_note(no: int, req: NoteRequest, conn=Depends(get_conn)):
    if repo.get_lead(conn, no) is None:
        raise HTTPException(status_code=404, detail="lead not found")
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty note")
    repo.add_note(conn, no, text)
    return repo.get_lead(conn, no)


@router.post("/leads/{no}/reply")
def mark_replied(no: int, req: ReplyRequest, conn=Depends(get_conn)):
    if req.channel not in REPLY_CHANNELS:
        raise HTTPException(status_code=400, detail="unknown channel")
    if repo.get_lead(conn, no) is None:
        raise HTTPException(status_code=404, detail="lead not found")
    repo.mark_replied(conn, no, req.channel)
    return {"ok": True}
