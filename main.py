"""
main.py — Analyst's Desk (Phase 6, Cluster 2 web merge).

Merges 3 of the cluster's 11 source projects into one FastAPI deployment:
SAM.gov Acquisition Intelligence Agent (/sam), FriendShore Supply Chain
De-Risking Engine (/friendshore), and SENTINEL Influence Operations
Detection Engine (/sentinel).

Unlike Arbor (Phase 6, Cluster 1), there is no shared business entity across
these three tools -- an acquisition opportunity isn't a narrative cluster
isn't a supply chain analysis -- so this merge unifies infrastructure only
(one process, one shared DB engine, one static-mount discipline, per-tool
route prefixes) and does not attempt a unifying entity-centric home page.
The landing page just links out to the three tools.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import APP_TITLE
from database import SessionLocal, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        import sam.router as sam_router
        import friendshore.router as friendshore_router
        import sentinel.seed_data as sentinel_seed_data

        sam_router.load_seed_data(db)
        friendshore_router.load_seed_data(db)
        sentinel_seed_data.load_seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan)

# Per-tool static mounts -- each tool's original bare "/static" mount would
# collide if all three were mounted at once, same class of conflict Arbor
# hit and resolved the same way (per-tool static subpaths).
app.mount("/static/sam", StaticFiles(directory="static/sam"), name="static_sam")
app.mount("/static/friendshore", StaticFiles(directory="static/friendshore"), name="static_friendshore")
app.mount("/static/sentinel", StaticFiles(directory="static/sentinel"), name="static_sentinel")

_landing_templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return _landing_templates.TemplateResponse(request, "landing.html", {"app_title": APP_TITLE})


from sam.router import router as sam_router
from friendshore.router import router as friendshore_router
from sentinel.router import router as sentinel_router

app.include_router(sam_router)
app.include_router(friendshore_router)
app.include_router(sentinel_router)
