"""Narrative clustering engine — groups articles by keyword overlap and updates cluster stats."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from sentinel.config import CLUSTER_KEYWORD_OVERLAP, VELOCITY_WINDOW_HOURS
from sentinel.models import Article, NarrativeCluster


def _keyword_overlap(a: list[str], b: list[str]) -> int:
    return len(set(k.lower() for k in a) & set(k.lower() for k in b))


def _threat_level(cluster: NarrativeCluster) -> str:
    if cluster.adversary_count >= 3 and cluster.velocity_score >= 0.4:
        return "HIGH"
    if cluster.adversary_count >= 2 or cluster.velocity_score >= 0.25:
        return "MEDIUM"
    return "LOW"


def _velocity(cluster: NarrativeCluster, db: Session) -> float:
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=VELOCITY_WINDOW_HOURS)
    recent = (
        db.query(Article)
        .filter(Article.cluster_id == cluster.id, Article.fetched_at >= window_start)
        .count()
    )
    if cluster.article_count == 0:
        return 0.0
    return round(recent / cluster.article_count, 3)


def cluster_article(article: Article, db: Session) -> NarrativeCluster:
    """Assign article to best matching cluster or create a new one."""
    if not article.keywords:
        label = article.title[:200]
        cluster = NarrativeCluster(label=label, summary=article.narrative_summary or label)
        db.add(cluster)
        db.flush()
        article.cluster_id = cluster.id
        _update_cluster_stats(cluster, db)
        return cluster

    # Find best matching existing cluster
    best_cluster: NarrativeCluster | None = None
    best_overlap = 0

    existing = db.query(NarrativeCluster).all()
    for c in existing:
        # Gather all keywords from articles in this cluster
        cluster_keywords: list[str] = []
        for a in c.articles:
            cluster_keywords.extend(a.keywords)
        overlap = _keyword_overlap(article.keywords, cluster_keywords)
        if overlap > best_overlap:
            best_overlap = overlap
            best_cluster = c

    if best_cluster and best_overlap >= CLUSTER_KEYWORD_OVERLAP:
        article.cluster_id = best_cluster.id
        _update_cluster_stats(best_cluster, db)
        return best_cluster

    # Create new cluster
    cluster = NarrativeCluster(
        label=article.title[:200],
        summary=article.narrative_summary or article.title[:200],
        first_seen=article.published_at or datetime.now(timezone.utc).replace(tzinfo=None),
        last_seen=article.published_at or datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(cluster)
    db.flush()
    article.cluster_id = cluster.id
    _update_cluster_stats(cluster, db)
    return cluster


def _update_cluster_stats(cluster: NarrativeCluster, db: Session) -> None:
    articles = db.query(Article).filter(Article.cluster_id == cluster.id).all()
    cluster.article_count = len(articles)
    cluster.adversary_count = sum(1 for a in articles if a.outlet_type == "adversary")
    cluster.baseline_count = sum(1 for a in articles if a.outlet_type == "baseline")
    cluster.social_count = sum(1 for a in articles if a.outlet_type == "social")

    dates = [a.published_at for a in articles if a.published_at]
    if dates:
        cluster.first_seen = min(dates)
        cluster.last_seen = max(dates)

    cluster.velocity_score = _velocity(cluster, db)
    cluster.threat_level = _threat_level(cluster)


def run_clustering(db: Session) -> dict:
    """Cluster all analyzed but unclustered articles."""
    unclustered = (
        db.query(Article)
        .filter(Article.is_analyzed == True, Article.cluster_id == None)
        .all()
    )
    clustered_count = 0
    for article in unclustered:
        cluster_article(article, db)
        clustered_count += 1

    # Refresh stats on all clusters
    for cluster in db.query(NarrativeCluster).all():
        _update_cluster_stats(cluster, db)

    db.commit()
    return {"clustered": clustered_count}
