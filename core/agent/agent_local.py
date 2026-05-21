import asyncio
import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

from core.agent.agent import main

LOCAL_BASE_URL = "http://127.0.0.1:8000"

if __name__ == "__main__":

    try:
        asyncio.run(main(LOCAL_BASE_URL))

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)