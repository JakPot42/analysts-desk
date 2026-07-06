"""
database.py — shared SQLAlchemy engine and session plumbing for the merged
Analyst's Desk web app.

One shared engine/DB (same "one deployment" pattern Arbor used), but --
unlike Arbor -- there is no shared business entity across sam/friendshore/
sentinel, so this file only unifies infrastructure (one engine, one Base,
one get_db dependency), not data. Each tool's tables are namespaced with a
tool prefix (sam_*, friendshore_*, sentinel_*) to avoid the real table-name
collision found during porting: sam_agent's Analysis model and friendshore's
SupplyChainAnalysis model both used __tablename__ = "analyses".
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    # Import every tool's models so they register on Base.metadata before create_all.
    import sam.models  # noqa: F401
    import friendshore.models  # noqa: F401
    import sentinel.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
