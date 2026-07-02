from fastapi import APIRouter, Depends, HTTPException

from app import repository as repo
from app.main_deps import get_conn
from app.models import Lead

router = APIRouter(prefix="/api")


@router.get("/leads", response_model=list[Lead])
def list_leads(country: str | None = None, channel: str | None = None,
               status: str | None = None, search: str | None = None, conn=Depends(get_conn)):
    return repo.list_leads(conn, country=country, channel=channel, status=status, search=search)


@router.get("/leads/{no}", response_model=Lead)
def get_lead(no: int, conn=Depends(get_conn)):
    lead = repo.get_lead(conn, no)
    if lead is None:
        raise HTTPException(status_code=404, detail="lead not found")
    return lead
