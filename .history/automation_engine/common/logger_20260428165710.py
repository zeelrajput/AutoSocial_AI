import sys


def clean_log(message):
    """
    Always show clean user-friendly logs,
    even when stdout is hidden.
    """
    sys.__stdout__.write(str(message) + "\n")
    sys.__stdout__.flush()


def log(message):
    """
    Debug log. Keep hidden during silent mode.
    """
    print(message)