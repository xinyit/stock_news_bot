import asyncio
from dotenv import load_dotenv

load_dotenv()

from main import send_digest

if __name__ == "__main__":
    asyncio.run(send_digest())