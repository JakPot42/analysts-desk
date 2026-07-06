"""
sam/router.py — routes for the SAM.gov Acquisition Intelligence Agent, ported
from sam_agent's main.py into an APIRouter mounted at /sam.

Route map (all under /sam)
---------------------------
GET  /sam/                          Search form
GET  /sam/search?q=...              Search results from SAM.gov
GET  /sam/opportunity/{notice_id}   Opportunity detail + Analyze button
POST /sam/analyze/{notice_id}       Run Claude analysis, redirect to result
GET  /sam/analysis/{analysis_id}    Compliance matrix view
GET  /sam/history                   Previously analyzed opportunities
POST /sam/seed                      Re-seed demo data
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from sam.claude_analyst import AnalysisError, analyze_opportunity
from sam.config import APP_TITLE, DEMO_BANNER, DEMO_MODE, SAM_API_KEY
from sam.models import Analysis, Opportunity
from sam.seed_data import DEMO_ANALYSES, DEMO_OPPORTUNITIES
from shared.sam_gov_client import (
    SAMAPIError,
    build_opportunity_text,
    get_opportunity,
    search_opportunities,
)

router = APIRouter(prefix="/sam")
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    app_title=APP_TITLE,
    demo_mode=DEMO_MODE,
    demo_banner=DEMO_BANNER,
)


def load_seed_data(db: Session) -> None:
    analysis_lookup = {a["notice_id"]: a for a in DEMO_ANALYSES}
    for opp_data in DEMO_OPPORTUNITIES:
        if db.scalar(select(Opportunity).where(Opportunity.notice_id == opp_data["notice_id"])):
            continue
        opp = Opportunity(
            notice_id=opp_data["notice_id"],
            title=opp_data["title"],
            solicitation_number=opp_data.get("solicitation_number"),
            agency=opp_data.get("agency"),
            naics_code=opp_data.get("naics_code"),
            set_aside=opp_data.get("set_aside"),
            posted_date=opp_data.get("posted_date"),
            response_deadline=opp_data.get("response_deadline"),
            ui_link=opp_data.get("ui_link"),
            description=opp_data.get("description"),
            raw_json=json.dumps(opp_data),
        )
        db.add(opp)
        db.flush()
        if opp_data["notice_id"] in analysis_lookup:
            a = analysis_lookup[opp_data["notice_id"]]
            db.add(Analysis(
                opportunity_id=opp.id,
                summary=a.get("summary"),
                agency=a.get("agency"),
                estimated_value=a.get("estimated_value"),
                period_of_performance=a.get("period_of_performance"),
                place_of_performance=a.get("place_of_performance"),
                clearance_required=a.get("clearance_required"),
                cmmc_level=a.get("cmmc_level"),
                set_aside=a.get("set_aside"),
                bottom_line=a.get("bottom_line"),
                _key_requirements=json.dumps(a.get("key_requirements", [])),
                _evaluation_criteria=json.dumps(a.get("evaluation_criteria", [])),
                _compliance_flags=json.dumps(a.get("compliance_flags", [])),
                _capability_bullets=json.dumps(a.get("capability_bullets", [])),
                raw_response=json.dumps(a),
            ))
    db.commit()


# --------------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "sam/index.html", {})


@router.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = "", db: Session = Depends(get_db)):
    if not q.strip():
        return RedirectResponse(url="/sam/")

    error = None
    opportunities = []
    total = 0

    try:
        data = search_opportunities(q.strip(), api_key=SAM_API_KEY)
        opportunities = data.get("opportunitiesData", [])
        total = data.get("totalRecords", 0)
    except SAMAPIError as exc:
        error = str(exc)

    return templates.TemplateResponse(request, "sam/results.html", {
        "query": q,
        "opportunities": opportunities,
        "total": total,
        "error": error,
    })


# --------------------------------------------------------------------------- #
# Opportunity detail
# --------------------------------------------------------------------------- #
@router.get("/opportunity/{notice_id}", response_class=HTMLResponse)
def opportunity_detail(notice_id: str, request: Request, db: Session = Depends(get_db)):
    opp_row = db.scalar(select(Opportunity).where(Opportunity.notice_id == notice_id))

    if opp_row is None:
        try:
            raw = get_opportunity(notice_id, api_key=SAM_API_KEY)
        except SAMAPIError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        if raw is None:
            raise HTTPException(status_code=404, detail="Opportunity not found on SAM.gov.")

        opp_row = Opportunity(
            notice_id=notice_id,
            title=raw.get("title", ""),
            solicitation_number=raw.get("solicitationNumber"),
            agency=raw.get("fullParentPathName") or raw.get("organizationHierarchy"),
            naics_code=raw.get("naicsCode"),
            set_aside=raw.get("typeOfSetAside"),
            posted_date=raw.get("postedDate"),
            response_deadline=raw.get("responseDeadLine"),
            ui_link=raw.get("uiLink"),
            description=raw.get("description"),
            raw_json=json.dumps(raw),
        )
        db.add(opp_row)
        db.commit()
        db.refresh(opp_row)

    return templates.TemplateResponse(request, "sam/opportunity.html", {
        "opp": opp_row,
        "has_analysis": opp_row.latest_analysis is not None,
        "analysis_id": opp_row.latest_analysis.id if opp_row.latest_analysis else None,
    })


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
@router.post("/analyze/{notice_id}")
def analyze(notice_id: str, request: Request, db: Session = Depends(get_db)):
    opp_row = db.scalar(select(Opportunity).where(Opportunity.notice_id == notice_id))
    if opp_row is None:
        raise HTTPException(status_code=404, detail="Opportunity not in cache. View it first.")

    raw_opp = json.loads(opp_row.raw_json) if opp_row.raw_json else {}
    opp_text = build_opportunity_text(raw_opp)

    try:
        result = analyze_opportunity(opp_text)
    except AnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    analysis = Analysis(
        opportunity_id=opp_row.id,
        summary=result.get("summary"),
        agency=result.get("agency"),
        estimated_value=result.get("estimated_value"),
        period_of_performance=result.get("period_of_performance"),
        place_of_performance=result.get("place_of_performance"),
        clearance_required=result.get("clearance_required"),
        cmmc_level=result.get("cmmc_level"),
        set_aside=result.get("set_aside"),
        bottom_line=result.get("bottom_line"),
        _key_requirements=json.dumps(result.get("key_requirements", [])),
        _evaluation_criteria=json.dumps(result.get("evaluation_criteria", [])),
        _compliance_flags=json.dumps(result.get("compliance_flags", [])),
        _capability_bullets=json.dumps(result.get("capability_statement_bullets", [])),
        raw_response=json.dumps(result),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return RedirectResponse(url=f"/sam/analysis/{analysis.id}", status_code=303)


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
def analysis_view(analysis_id: int, request: Request, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return templates.TemplateResponse(request, "sam/analysis.html", {"analysis": analysis})


# --------------------------------------------------------------------------- #
# History
# --------------------------------------------------------------------------- #
@router.get("/history", response_class=HTMLResponse)
def history(request: Request, db: Session = Depends(get_db)):
    analyses = db.scalars(
        select(Analysis).order_by(Analysis.created_at.desc()).limit(50)
    ).all()
    return templates.TemplateResponse(request, "sam/history.html", {"analyses": analyses})


# --------------------------------------------------------------------------- #
# Demo seed
# --------------------------------------------------------------------------- #
@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    """Load pre-built demo opportunities and analyses (idempotent)."""
    load_seed_data(db)
    return RedirectResponse(url="/sam/history", status_code=303)
