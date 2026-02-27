# bot/fetcher.py
import feedparser
import json
import os
from datetime import datetime, timezone, timedelta

# ── RSS feeds (all free, no auth needed) ──────────────────────────
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.wired.com/feed/rss",
    "https://hnrss.org/frontpage",                  # Hacker News
    "https://feeds.feedburner.com/venturebeat/SZYF", # VentureBeat
]

POSTED_IDS_PATH = "data/posted_ids.json"
MAX_AGE_HOURS = 24  # only fetch news from last 24 hours


def load_posted_ids():
    """Load list of already-posted article IDs."""
    if not os.path.exists(POSTED_IDS_PATH):
        return []
    with open(POSTED_IDS_PATH, "r") as f:
        return json.load(f)


def save_posted_ids(ids: list):
    """Save updated posted IDs list back to file."""
    # Keep only last 500 to prevent file bloat
    ids = ids[-500:]
    with open(POSTED_IDS_PATH, "w") as f:
        json.dump(ids, f, indent=2)


def is_recent(entry) -> bool:
    """Check if article was published within last MAX_AGE_HOURS."""
    if not hasattr(entry, "published_parsed") or entry.published_parsed is None:
        return True  # if no date, include it anyway
    pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    return pub_time >= cutoff


def fetch_latest_articles(max_articles: int = 5) -> list:
    """
    Fetch latest unposted articles from all RSS feeds.
    Returns a list of article dicts.
    """
    posted_ids = load_posted_ids()
    articles = []

    for feed_url in RSS_FEEDS:
        print(f"[FETCHER] Checking feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[FETCHER] Failed to parse {feed_url}: {e}")
            continue

        for entry in feed.entries:
            # Build a unique ID from the article link
            article_id = entry.get("link", entry.get("id", ""))

            # Skip if already posted
            if article_id in posted_ids:
                continue

            # Skip if too old
            if not is_recent(entry):
                continue

            # Extract summary (strip HTML tags roughly)
            summary = entry.get("summary", "")
            summary = summary.replace("<p>", " ").replace("</p>", " ")
            # Basic tag strip
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = summary[:500]  # cap length

            article = {
                "id": article_id,
                "title": entry.get("title", "No title"),
                "link": article_id,
                "summary": summary,
                "source": feed.feed.get("title", "Unknown Source"),
                "published": entry.get("published", "Unknown date"),
            }

            articles.append(article)

            # Stop once we have enough candidates
            if len(articles) >= max_articles * 3:
                break

        if len(articles) >= max_articles * 3:
            break

    # Sort by newest first (best effort)
    articles = articles[:max_articles]
    print(f"[FETCHER] Found {len(articles)} new articles")
    return articles


if __name__ == "__main__":
    # Quick test
    arts = fetch_latest_articles()
    for a in arts:
        print(f"\n→ {a['title']}\n  {a['link']}")