import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read os.environ at import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from telegram.constants import ParseMode

from config import STOCKS, DIGEST_HOUR, DIGEST_MINUTE, TIMEZONE
from news_fetcher import fetch_stock_news
from summarizer import summarize_all_news

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

def split_for_telegram(text: str, limit: int = 4000) -> list[str]:
    """Split text into Telegram-safe chunks, breaking on section dividers."""
    if len(text) <= limit:
        return [text]

    parts = text.split("———")
    chunks, current = [], ""
    for part in parts:
        candidate = (current + "———" + part) if current else part
        if len(candidate) > limit:
            if current:
                chunks.append(current.strip())
            current = part
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks


async def send_digest():
    """Fetch news for all stocks, summarize once, and send to the channel."""
    bot = Bot(token=BOT_TOKEN)
    today = datetime.now().strftime("%A, %B %d %Y")

    log.info(f"Fetching news for {len(STOCKS)} stocks...")
    stocks_data = {ticker: fetch_stock_news(ticker) for ticker in STOCKS}

    log.info("Generating combined summary (1 API call)...")
    digest_body = summarize_all_news(stocks_data)

    full_message = f"🌅 *Good morning! Today's Stock Bites [{today}*\n\n{digest_body}]"

    for chunk in split_for_telegram(full_message):
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        except Exception as e:
            log.error(f"Failed to send message chunk: {e}")
        await asyncio.sleep(1)

    log.info("Digest sent.")


async def main():
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_digest,
        CronTrigger(hour=DIGEST_HOUR, minute=DIGEST_MINUTE, timezone=TIMEZONE),
        id="morning_digest",
        name="Morning Stock Digest",
    )
    scheduler.start()
    log.info(f"Scheduler started. Digest runs daily at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} {TIMEZONE}")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())