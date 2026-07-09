import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.main_deps import get_conn  # re-exported for tests / dependency overrides
from app.api import leads as leads_api
from app.api import stats as stats_api
from app.api import send as send_api
from app.api import discover as discover_api
from app.api import channels as channels_api
from app.api import templates as templates_api
from app.api import sequences as sequences_api
from app.api import replies as replies_api

app = FastAPI(title="Outreach Tool")
app.include_router(leads_api.router)
app.include_router(stats_api.router)
app.include_router(send_api.router)
app.include_router(discover_api.router)
app.include_router(channels_api.router)
app.include_router(templates_api.router)
app.include_router(sequences_api.router)
app.include_router(replies_api.router)

_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")
