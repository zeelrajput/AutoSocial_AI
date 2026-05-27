import asyncio
import sys
import os
from pathlib import Path

# -------------------------------------------------
# FIX PROJECT ROOT FOR PYTHON + EXE
# -------------------------------------------------

if getattr(sys, 'frozen', False):
    # EXE mode
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # Normal python mode
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Add project root to python path
sys.path.insert(0, str(PROJECT_ROOT))

# Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

# Import AFTER django setup
from core.agent.agent import main

LIVE_BASE_URL = "https://agents.zettalgor.com"

# -------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(main(LIVE_BASE_URL))

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)