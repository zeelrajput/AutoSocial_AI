import asyncio
from core.agent.agent import main

LIVE_BASE_URL = "https://chat.zettalgor.com"

if __name__ == "__main__":
    asyncio.run(main(LIVE_BASE_URL))

    