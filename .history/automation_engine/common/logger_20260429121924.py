import sys

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