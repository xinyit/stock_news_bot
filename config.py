# Tickers to track
import os

STOCKS = os.environ.get("STOCKS", "AAPL,GOOGL,AMZN,MSFT,TSLA").split(",")

# How many articles to fetch per stock
MAX_ARTICLES_PER_STOCK = 4

# What time to send the digest (24h format, SGT = UTC+8)
DIGEST_HOUR = 8
DIGEST_MINUTE = 45
TIMEZONE = "Asia/Singapore"