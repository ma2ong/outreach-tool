from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app import jobs, verify
from app.db import connect
from app.main_deps import DB_PATH as _DB_PATH

router = APIRouter(prefix="/api")

DB_PATH = _DB_PATH
RESOLVER = None  # injectable in tests; None -> real DNS


class VerifyRequest(BaseModel):
    lead_nos: list[int] | None = None


def _run(job_id: str, lead_nos):
    conn = connect(DB_PATH)
    try:
        resolver = RESOLVER or verify.default_resolver
        result = verify.verify_leads(conn, lead_nos, resolve_domain=resolver)
        jobs.finish(job_id, result)
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.post("/leads/verify")
def verify_emails(req: VerifyRequest, background: BackgroundTasks):
    job_id = jobs.create(total=len(req.lead_nos) if req.lead_nos else 0)
    background.add_task(_run, job_id, req.lead_nos)
    return {"job_id": job_id}


@router.get("/leads/verify/jobs/{job_id}")
def verify_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job
