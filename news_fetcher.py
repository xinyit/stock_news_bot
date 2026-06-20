import feedparser
import httpx
from datetime import datetime, timezone, timedelta
from config import MAX_ARTICLES_PER_STOCK


def fetch_stock_news(ticker: str) -> list[dict]:
    """Fetch recent news articles for a stock ticker via Yahoo Finance RSS."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    try:
        # feedparser can be slow; use httpx with a timeout
        response = httpx.get(url, timeout=10, follow_redirects=True)
        feed = feedparser.parse(response.text)
    except Exception as e:
        print(f"[{ticker}] Failed to fetch feed: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    articles = []

    for entry in feed.entries[:MAX_ARTICLES_PER_STOCK * 2]:  # fetch extra, filter by date
        # Parse publish date if available
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        # Skip articles older than 24h if date is available
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