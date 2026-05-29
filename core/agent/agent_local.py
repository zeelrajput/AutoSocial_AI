import asyncio
import sys
import os
from pathlib import Path

# -------------------------------------------------
# FIX FOR EXE + DJANGO
# -------------------------------------------------

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(BASE_DIR))

# Django settings
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

import django
django.setup()

# Import AFTER setup
from core.agent.agent import main

LOCAL_BASE_URL = "http://127.0.0.1:8000"

# -------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main(LOCAL_BASE_URL))

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)