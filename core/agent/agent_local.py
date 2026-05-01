import asyncio
from core.agent.agent import main

LOCAL_BASE_URL = "http://127.0.0.1:8000"

if __name__ == "__main__":
    asyncio.run(main(LOCAL_BASE_URL))