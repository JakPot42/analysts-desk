"""RSS and Reddit ingestion — fetches articles, deduplicates, stores in DB."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx
from sqlalchemy.orm import Session

from sentinel.config import RSS_SOURCES, REDDIT_SUBREDDITS
from sentinel.models import Article


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _parse_date(entry: Any) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                import time
                ts = time.mktime(val)
                return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
    if hasattr(entry, "published"):
        try:
            return parsedate_to_datetime(entry.published).replace(tzinfo=None)
        except Exception:
            pass
    return None


def _url_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def fetch_rss_source(name: str, url: str, outlet_type: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []

    articles = []
    for entry in feed.entries[:25]:
        link = getattr(entry, "link", "") or getattr(entry, "id", "")
        if not link:
            continue
        title = _clean_html(getattr(entry, "title", ""))
        body = _clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))
        articles.append({
            "source_name": name,
            "outlet_type": outlet_type,
            "url": link,
            "title": title,
            "body_text": body[:2000],
            "published_at": _parse_date(entry),
        })
    return articles


def fetch_reddit_source(subreddit: str, limit: int = 25) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": "SENTINEL-IO-Monitor/1.0 (defense research demo)"}
    try:
        resp = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        data = resp.json()
    except Exception:
        return []

    articles = []
    for post in data.get("data", {}).get("children", []):
        p = post.get("data", {})
        url_val = p.get("url", "")
        title = p.get("title", "")
        body = p.get("selftext", "") or ""
        created = p.get("created_utc")
        pub_at = datetime.fromtimestamp(created, tz=timezone.utc).replace(tzinfo=None) if created else None
        permalink = "https://www.reddit.com" + p.get("permalink", "")
        articles.append({
            "source_name": f"Reddit r/{subreddit}",
            "outlet_type": "social",
            "url": permalink,
            "title": title,
            "body_text": (f"[links to: {url_val}] " + body)[:2000],
            "published_at": pub_at,
        })
    return articles


def ingest_all(db: Session) -> dict:
    existing_urls = {row[0] for row in db.query(Article.url).all()}
    new_count = 0
    skipped = 0

    for name, url, outlet_type in RSS_SOURCES:
        for article_data in fetch_rss_source(name, url, outlet_type):
            if article_data["url"] in existing_urls:
                skipped += 1
                continue
            db.add(Article(**article_data))
            existing_urls.add(article_data["url"])
            new_count += 1

    for subreddit in REDDIT_SUBREDDITS:
        for article_data in fetch_reddit_source(subreddit):
            if article_data["url"] in existing_urls:
                skipped += 1
                continue
            db.add(Article(**article_data))
            existing_urls.add(article_data["url"])
            new_count += 1

    db.commit()
    return {"ingested": new_count, "skipped": skipped}
