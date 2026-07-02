from fastapi import FastAPI

from app.main_deps import get_conn  # re-exported for tests / dependency overrides
from app.api import leads as leads_api
from app.api import stats as stats_api

app = FastAPI(title="Outreach Tool")
app.include_router(leads_api.router)
app.include_router(stats_api.router)
