import anthropic
import os

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Check Railway's Variables tab "
                "(or your local .env file) and redeploy."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def summarize_all_news(stocks_data: dict[str, list[dict]]) -> str:
    """Summarize news for all tracked stocks in a single Claude API call."""
    client = _get_client()

    sections = []
    for ticker, articles in stocks_data.items():
        if not articles:
            sections.append(f"## {ticker}\nNo recent articles found.")
            continue
        articles_text = "\n\n".join(
            f"Headline: {a['title']}\nDetails: {a['summary']}\n"
            f"Published: {a['published']}\nLink: {a['link']}"
            for a in articles
        )
        sections.append(f"## {ticker}\n{articles_text}")

    combined_input = "\n\n".join(sections)

    prompt = f"""You are a financial news summarizer. Below is recent news data for several stock tickers.

For EACH ticker, write a section formatted exactly like this:

📊 *{{TICKER}}*
- [2-3 short bullet points of key developments]
- Sentiment: 📈 Bullish / 📉 Bearish / ➡️ Neutral
🔗 [up to 2 source links as markdown links]

If a ticker has no news, write only:
📊 *{{TICKER}}*
No notable news in the last 24 hours.

Rules:
- Use Telegram Markdown (single asterisks for bold, not double asterisks)
- Keep each ticker section under 70 words
- Separate each ticker's section with a line containing only: ———
- No preamble, no closing remarks, no investment advice or disclaimers
- Go straight into the first ticker section

News data:
{combined_input}"""

    response = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()