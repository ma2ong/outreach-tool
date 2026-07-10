from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app import discovery, jobs, repository
from app.db import connect
from app.main_deps import DB_PATH as _DB_PATH, get_conn

router = APIRouter(prefix="/api")

DB_PATH = _DB_PATH
SEARCH_FN = None    # injectable in tests; None -> real search
ENRICH_FN = None    # injectable in tests; None -> real enrich
HARVEST_FN = None   # injectable in tests; None -> real harvest


class DiscoverRequest(BaseModel):
    query: str
    limit: int = 10


class PageDiscoverRequest(BaseModel):
    url: str
    limit: int = 40


class Candidate(BaseModel):
    company_en: str
    website: str | None = None
    email: str | None = None
    city: str | None = None
    phone: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    linkedin: str | None = None
    source: str | None = None
    icp_type: str | None = None
    fit_score: int | None = None


class ImportRequest(BaseModel):
    country: str | None = None
    candidates: list[Candidate]


def _run(job_id: str, query: str, limit: int):
    conn = connect(DB_PATH)
    try:
        cands = discovery.run_discovery(
            conn, query, limit, search_fn=SEARCH_FN, enrich_fn=ENRICH_FN,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, {"candidates": cands})
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


def _run_page(job_id: str, url: str, limit: int):
    conn = connect(DB_PATH)
    try:
        cands = discovery.run_page_discovery(
            conn, url, limit, harvest_fn=HARVEST_FN, enrich_fn=ENRICH_FN,
            on_progress=lambda done, total: jobs.update(job_id, done))
        jobs.finish(job_id, {"candidates": cands})
    except Exception as exc:  # noqa: BLE001
        jobs.fail(job_id, str(exc))
    finally:
        conn.close()


@router.post("/discover")
def discover(req: DiscoverRequest, background: BackgroundTasks):
    job_id = jobs.create(total=req.limit)
    background.add_task(_run, job_id, req.query, req.limit)
    return {"job_id": job_id}


@router.post("/discover/page")
def discover_page(req: PageDiscoverRequest, background: BackgroundTasks):
    if not req.url.strip().lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    job_id = jobs.create(total=req.limit)
    background.add_task(_run_page, job_id, req.url.strip(), req.limit)
    return {"job_id": job_id}


@router.get("/discover/jobs/{job_id}")
def discover_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.post("/leads/import")
def import_leads(req: ImportRequest, conn=Depends(get_conn)):
    from app import icp as icp_mod
    imported = 0
    for c in req.candidates:
        if c.website and repository.find_duplicate(conn, website=c.website, instagram=c.instagram, company_en=c.company_en):
            continue
        fit = "discovered"
        if c.icp_type and c.icp_type != "unknown":
            fit = f"{icp_mod.label(c.icp_type)} ({c.fit_score or 0})"
        no = repository.insert_lead(conn, {
            "company_en": c.company_en, "country": req.country, "city": c.city,
            "website": c.website, "email": c.email, "phone": c.phone,
            "instagram": c.instagram, "facebook": c.facebook, "linkedin": c.linkedin,
            "target_fit": fit})
        if c.icp_type and c.icp_type != "unknown":
            icp_mod.apply_to_lead(conn, no, {"icp_type": c.icp_type, "fit_score": c.fit_score or 0})
        imported += 1
    return {"imported": imported}
