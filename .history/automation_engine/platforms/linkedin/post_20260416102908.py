import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)

def _find_first_visible(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            print(f"LinkedIn selector matched: {selector}")
            return element
        except Exception:
            continue
    return None

def _find_first_clickable(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            print(f"LinkedIn clickable selector matched: {selector}")
            return element
        except Exception:
            continue
    return None

def post_to_linkedin(driver, post):
    """
    Create a text-only LinkedIn post.
    Excepts user to already be logged in.
    """
    try:
        print("Openinh LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(4)

        # step 1: Open post modal
        start_post_btn = _find_first_clickable(dr)
