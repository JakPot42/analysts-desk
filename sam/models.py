"""
sam/models.py — SQLAlchemy ORM models for the SAM.gov Acquisition Intelligence Agent.

Tables renamed with a sam_ prefix during the merge: the original __tablename__
"analyses" collided exactly with friendshore's SupplyChainAnalysis model,
which also used __tablename__ = "analyses". All three tools' tables are
now prefixed (sam_*, friendshore_*, sentinel_*) to remove that collision
and prevent any future one. No Python attribute/column names changed, so
seed_data.py, router.py, and claude_analyst.py needed no changes for this.
"""

from __future__ import annotations

import datetime as _dt
import json

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Opportunity(Base):
    __tablename__ = "sam_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notice_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    solicitation_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    agency: Mapped[str | None] = mapped_column(Text, nullable=True)
    naics_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    set_aside: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_deadline: Mapped[str | None] = mapped_column(Text, nullable=True)
    ui_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[_dt.datetime] = mapped_column(DateTime, server_default=func.now())

    analyses: Mapped[list[Analysis]] = relationship("Analysis", back_populates="opportunity")

    @property
    def latest_analysis(self) -> Analysis | None:
        return self.analyses[-1] if self.analyses else None


class Analysis(Base):
    __tablename__ = "sam_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(Integer, ForeignKey("sam_opportunities.id"))
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, server_default=func.now())

    # Top-level fields
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    agency: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_of_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    place_of_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    clearance_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    cmmc_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    set_aside: Mapped[str | None] = mapped_column(Text, nullable=True)
    bottom_line: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON-encoded lists
    _key_requirements: Mapped[str | None] = mapped_column("key_requirements", Text, nullable=True)
    _evaluation_criteria: Mapped[str | None] = mapped_column("evaluation_criteria", Text, nullable=True)
    _compliance_flags: Mapped[str | None] = mapped_column("compliance_flags", Text, nullable=True)
    _capability_bullets: Mapped[str | None] = mapped_column("capability_bullets", Text, nullable=True)

    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity: Mapped[Opportunity] = relationship("Opportunity", back_populates="analyses")

    @property
    def key_requirements(self) -> list:
        return json.loads(self._key_requirements) if self._key_requirements else []

    @property
    def evaluation_criteria(self) -> list:
        return json.loads(self._evaluation_criteria) if self._evaluation_criteria else []

    @property
    def compliance_flags(self) -> list:
        return json.loads(self._compliance_flags) if self._compliance_flags else []

    @property
    def capability_bullets(self) -> list:
        return json.loads(self._capability_bullets) if self._capability_bullets else []

    @property
    def executive_summary_flags(self) -> list:
        from sam.claude_analyst import build_executive_summary
        if not self.raw_response:
            return []
        try:
            return build_executive_summary(json.loads(self.raw_response))
        except Exception:
            return []
