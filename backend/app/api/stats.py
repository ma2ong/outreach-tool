from fastapi import APIRouter, Depends

from app import repository as repo
from app.main_deps import get_conn
from app.models import Stats

router = APIRouter(prefix="/api")


@router.get("/stats", response_model=Stats)
def get_stats(conn=Depends(get_conn)):
    return repo.stats(conn)
