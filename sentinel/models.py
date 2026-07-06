"""
sentinel/models.py — SQLAlchemy ORM models for SENTINEL.

Tables renamed with a sentinel_ prefix during the merge for consistency
with sam_* and friendshore_* (no actual collision existed for these five
table names, but every tool's tables are prefixed to remove any future
collision risk in one pass rather than fixing them one at a time as found).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Article(Base):
    __tablename__ = "sentinel_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100))
    outlet_type: Mapped[str] = mapped_column(String(20))  # adversary | baseline | social
    url: Mapped[str] = mapped_column(String(500), unique=True)
    title: Mapped[str] = mapped_column(String(500))
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    # Claude-extracted fields
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    narrative_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    _entities: Mapped[Optional[str]] = mapped_column("entities_json", Text, nullable=True)
    _keywords: Mapped[Optional[str]] = mapped_column("keywords_json", Text, nullable=True)
    _credibility_signals: Mapped[Optional[str]] = mapped_column("credibility_signals_json", Text, nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_divisive: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    cluster_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sentinel_narrative_clusters.id"), nullable=True)
    cluster: Mapped[Optional["NarrativeCluster"]] = relationship("NarrativeCluster", back_populates="articles")

    @property
    def entities(self) -> list[str]:
        return json.loads(self._entities) if self._entities else []

    @entities.setter
    def entities(self, val: list[str]) -> None:
        self._entities = json.dumps(val)

    @property
    def keywords(self) -> list[str]:
        return json.loads(self._keywords) if self._keywords else []

    @keywords.setter
    def keywords(self, val: list[str]) -> None:
        self._keywords = json.dumps(val)

    @property
    def credibility_signals(self) -> list[str]:
        return json.loads(self._credibility_signals) if self._credibility_signals else []

    @credibility_signals.setter
    def credibility_signals(self, val: list[str]) -> None:
        self._credibility_signals = json.dumps(val)


class NarrativeCluster(Base):
    __tablename__ = "sentinel_narrative_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(300))
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    velocity_score: Mapped[float] = mapped_column(Float, default=0.0)
    adversary_count: Mapped[int] = mapped_column(Integer, default=0)
    baseline_count: Mapped[int] = mapped_column(Integer, default=0)
    social_count: Mapped[int] = mapped_column(Integer, default=0)
    threat_level: Mapped[str] = mapped_column(String(10), default="LOW")  # HIGH | MEDIUM | LOW

    articles: Mapped[list[Article]] = relationship("Article", back_populates="cluster")
    ttp_tags: Mapped[list["TTPTag"]] = relationship("TTPTag", back_populates="cluster", cascade="all, delete-orphan")
    intel_reports: Mapped[list["IntelReport"]] = relationship(
        "IntelReport", secondary="sentinel_report_cluster_link", back_populates="clusters"
    )

    @property
    def spread_hours(self) -> float:
        if not self.first_seen or not self.last_seen:
            return 0.0
        delta = self.last_seen - self.first_seen
        return round(delta.total_seconds() / 3600, 1)

    @property
    def threat_badge_class(self) -> str:
        return {"HIGH": "badge-red", "MEDIUM": "badge-yellow", "LOW": "badge-green"}.get(self.threat_level, "badge-green")


class TTPTag(Base):
    __tablename__ = "sentinel_ttp_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(Integer, ForeignKey("sentinel_narrative_clusters.id"))
    ttp_id: Mapped[str] = mapped_column(String(20))
    ttp_name: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[str] = mapped_column(String(10))  # high | medium | low
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    cluster: Mapped[NarrativeCluster] = relationship("NarrativeCluster", back_populates="ttp_tags")

    @property
    def confidence_badge_class(self) -> str:
        return {"high": "badge-red", "medium": "badge-yellow", "low": "badge-green"}.get(self.confidence, "badge-green")


# Association table for many-to-many IntelReport ↔ NarrativeCluster
from sqlalchemy import Table, Column
report_cluster_link = Table(
    "sentinel_report_cluster_link",
    Base.metadata,
    Column("report_id", Integer, ForeignKey("sentinel_intel_reports.id")),
    Column("cluster_id", Integer, ForeignKey("sentinel_narrative_clusters.id")),
)


class IntelReport(Base):
    __tablename__ = "sentinel_intel_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ref_number: Mapped[str] = mapped_column(String(50))  # e.g. SENTINEL-2026-001
    title: Mapped[str] = mapped_column(String(300))
    subject: Mapped[str] = mapped_column(String(300))
    confidence_level: Mapped[str] = mapped_column(String(20))  # HIGH | MODERATE | LOW | UNASSESSED
    attribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    _key_findings: Mapped[Optional[str]] = mapped_column("key_findings_json", Text, nullable=True)
    full_text: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    clusters: Mapped[list[NarrativeCluster]] = relationship(
        "NarrativeCluster", secondary="sentinel_report_cluster_link", back_populates="intel_reports"
    )

    @property
    def key_findings(self) -> list[str]:
        return json.loads(self._key_findings) if self._key_findings else []

    @key_findings.setter
    def key_findings(self, val: list[str]) -> None:
        self._key_findings = json.dumps(val)

    @property
    def confidence_badge_class(self) -> str:
        return {
            "HIGH": "badge-red", "MODERATE": "badge-yellow",
            "LOW": "badge-green", "UNASSESSED": "badge-gray"
        }.get(self.confidence_level, "badge-gray")
