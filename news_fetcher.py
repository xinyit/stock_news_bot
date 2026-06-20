import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from config import MAX_ARTICLES_PER_STOCK

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_stock_news(ticker: str) -> list[dict]:
    """Fetch recent news articles for a stock ticker via Yahoo Finance RSS."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    try:
        response = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        response.raise_for_status()  # surface non-200s explicitly instead of silently parsing empty content
        feed = feedparser.parse(response.text)
    except httpx.HTTPStatusError as e:
        print(f"[{ticker}] HTTP error {e.response.status_code}: {e}")
        return []
    except Exception as e:
        print(f"[{ticker}] Failed to fetch feed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    articles = []

    for entry in feed.entries[:MAX_ARTICLES_PER_STOCK * 2]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        if published and published < cutoff:
            continue

        articles.append({
            "title": entry.get("title", "No title"),
            "summary": entry.get("summary", ""),
            "link": entry.get("link", ""),
            "published": published.strftime("%b %d, %I:%M %p UTC") if published else "Unknown",
        })

        if len(articles) >= MAX_ARTICLES_PER_STOCK:
            break

    return articles