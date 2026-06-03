import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEBUG = False


def clean_log(message):
    """
    User-visible clean terminal log.
    Always visible, even when automation output is hidden.
    """
    sys.__stdout__.write(str(message) + "\n")
    sys.__stdout__.flush()


def debug_log(message):
    """
    Developer/debug log.
    Only visible when DEBUG = True.
    """
    if DEBUG:
        sys.__stdout__.write(str(message) + "\n")
        sys.__stdout__.flush()


BASE_DIR = Path(__file__).resolve().parents[3]
_logger_cache = {}


def get_log_dir(platform):
    platform = platform.lower().strip()
    return BASE_DIR / "core" / "automation_engine" / "platforms" / platform / "logs"


def cleanup_old_logs(log_dir, days=2):
    cutoff = datetime.now() - timedelta(days=days)

    for log_file in log_dir.glob("*.log"):
        try:
            modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)

            if modified_time < cutoff:
                log_file.unlink()
        except Exception:
            pass


def get_platform_logger(platform):
    platform = platform.lower().strip()

    log_dir = get_log_dir(platform)
    log_dir.mkdir(parents=True, exist_ok=True)

    cleanup_old_logs(log_dir, days=2)

    log_path = log_dir / f"{platform}.log"

    cache_key = f"{platform}:{log_path}"

    if cache_key in _logger_cache:
        return _logger_cache[cache_key]

    logger = logging.getLogger(f"autosocial.{platform}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    _logger_cache[cache_key] = logger
    return logger