import sys

# Skip Celery import inside EXE
if not getattr(sys, "frozen", False):
    from .celery import app as celery_app

    __all__ = ("celery_app",)