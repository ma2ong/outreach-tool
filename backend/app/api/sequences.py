from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import sequences as seq
from app.main_deps import get_conn
from app.models import DueItem, Sequence, SequenceStep

router = APIRouter(prefix="/api/sequences")


class StepIn(BaseModel):
    day_offset: int = 0
    subject: str | None = None
    body: str
    image: str | None = None


class SequenceCreate(BaseModel):
    name: str
    channel: str
    steps: list[StepIn]


class EnrollRequest(BaseModel):
    lead_nos: list[int]


class AdvanceRequest(BaseModel):
    enrollment_ids: list[int]


@router.get("", response_model=list[Sequence])
def list_sequences(conn=Depends(get_conn)):
    return [Sequence(**s) for s in seq.list_sequences(conn)]


@router.post("", response_model=Sequence)
def create_sequence(req: SequenceCreate, conn=Depends(get_conn)):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="name required")
    if req.channel not in ("email", "whatsapp", "instagram"):
        raise HTTPException(status_code=400, detail="unsupported channel")
    if not req.steps or any(not s.body.strip() for s in req.steps):
        raise HTTPException(status_code=400, detail="each step needs a body")
    sid = seq.create_sequence(conn, req.name.strip(), req.channel,
                              [s.model_dump() for s in req.steps])
    return Sequence(**seq.get_sequence(conn, sid))


@router.get("/due", response_model=list[DueItem])
def due(channel: str | None = None, conn=Depends(get_conn)):
    return [DueItem(**d) for d in seq.due_queue(conn, channel)]


@router.post("/{sid}/enroll")
def enroll(sid: int, req: EnrollRequest, conn=Depends(get_conn)):
    if seq.get_sequence(conn, sid) is None:
        raise HTTPException(status_code=404, detail="sequence not found")
    enrolled = seq.enroll_leads(conn, sid, req.lead_nos)
    return {"enrolled": enrolled, "selected": len(req.lead_nos)}


@router.post("/advance")
def advance(req: AdvanceRequest, conn=Depends(get_conn)):
    for eid in req.enrollment_ids:
        seq.advance_enrollment(conn, eid)
    return {"advanced": len(req.enrollment_ids)}
