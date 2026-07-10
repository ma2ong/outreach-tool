from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import repository as repo
from app.main_deps import get_conn
from app.models import Template

router = APIRouter(prefix="/api")


class TemplateCreate(BaseModel):
    name: str
    channel: str
    subject: str | None = None
    body: str
    lang: str | None = None


@router.get("/templates", response_model=list[Template])
def list_templates(channel: str | None = None, conn=Depends(get_conn)):
    return repo.list_templates(conn, channel=channel)


@router.post("/templates", response_model=Template)
def create_template(req: TemplateCreate, conn=Depends(get_conn)):
    if not req.name.strip() or not req.body.strip():
        raise HTTPException(status_code=400, detail="name and body required")
    tid = repo.add_template(conn, req.name.strip(), req.channel, req.subject, req.body, req.lang)
    return next(t for t in repo.list_templates(conn) if t.id == tid)


@router.delete("/templates/{tid}")
def delete_template(tid: int, conn=Depends(get_conn)):
    if not repo.delete_template(conn, tid):
        raise HTTPException(status_code=404, detail="template not found")
    return {"ok": True}
