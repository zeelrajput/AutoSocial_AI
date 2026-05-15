import asyncio
import sys
from pathlib import Path

# Fix path for direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agent.agent import main

LOCAL_BASE_URL = "http://127.0.0.1:8000"

if __name__ == "__main__":
    try:
        asyncio.run(main(LOCAL_BASE_URL))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)