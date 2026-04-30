import time


def type_like_human(element, text, delay=0.05):
    for char in text:
        element.send_keys(char)
        time.sleep(delay)