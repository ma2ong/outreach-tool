import datetime
import glob
import os
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main_deps import get_conn, DB_PATH  # re-exported for tests / dependency overrides
from app.db import connect, init_schema
from app.api import leads as leads_api
from app.api import stats as stats_api
from app.api import send as send_api
from app.api import discover as discover_api
from app.api import channels as channels_api
from app.api import templates as templates_api
from app.api import sequences as sequences_api
from app.api import replies as replies_api
from app.api import verify as verify_api
from app.api import mailboxes as mailboxes_api
from app.api import classify as classify_api
from app.api import products as products_api
from app.api import inbox as inbox_api

BACKUP_KEEP = 14


def backup_db(db_path: str = DB_PATH) -> str | None:
    """Copy the DB into backups/ once per day; prune to the newest BACKUP_KEEP files."""
    if not os.path.isfile(db_path):
        return None
    bdir = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(bdir, exist_ok=True)
    dest = os.path.join(bdir, f"outreach-{datetime.date.today().isoformat()}.db")
    if not os.path.exists(dest):
        shutil.copy2(db_path, dest)
    for old in sorted(glob.glob(os.path.join(bdir, "outreach-*.db")))[:-BACKUP_KEEP]:
        os.remove(old)
    return dest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent: CREATE TABLE IF NOT EXISTS + additive column migration, so an
    # existing outreach.db picks up new tables/columns on upgrade without re-running migrate.
    from app.dedupe import normalize_all_websites
    backup_db()  # the lead base is the business asset — snapshot before touching it
    conn = connect(DB_PATH)
    try:
        init_schema(conn)
        normalize_all_websites(conn)  # idempotent data fix: consistent website form
    finally:
        conn.close()
    yield


app = FastAPI(title="Outreach Tool", lifespan=lifespan)
app.include_router(leads_api.router)
app.include_router(stats_api.router)
app.include_router(send_api.router)
app.include_router(discover_api.router)
app.include_router(channels_api.router)
app.include_router(templates_api.router)
app.include_router(sequences_api.router)
app.include_router(replies_api.router)
app.include_router(verify_api.router)
app.include_router(mailboxes_api.router)
app.include_router(classify_api.router)
app.include_router(products_api.router)
app.include_router(inbox_api.router)

_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")
