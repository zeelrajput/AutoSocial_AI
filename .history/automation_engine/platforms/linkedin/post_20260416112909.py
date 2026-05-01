import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def _find_first_clickable_css(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            print(f"LinkedIn clickable CSS matched: {selector}")
            return element
        except Exception:
            continue
    return None


def _find_first_clickable_xpath(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_clickable(driver, By.XPATH, selector, timeout=timeout)
            print(f"LinkedIn clickable XPath matched: {selector}")
            return element
        except Exception:
            continue
    return None


START_POST_XPATHS = [
    "//button[contains(., 'Start a post')]",
    "//button[contains(@aria-label, 'Start a post')]",
    "//span[contains(., 'Start a post')]/ancestor::button[1]",
]


def post_to_linkedin(driver, post):
    try:
        print("Opening LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(6)

        print("Finding start post button...")
        start_post_btn = _find_first_clickable_css(driver, START_POST_SELECTORS, timeout=20)

        if not start_post_btn:
            start_post_btn = _find_first_clickable_xpath(driver, START_POST_XPATHS, timeout=10)

        if not start_post_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"LinkedIn start post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, start_post_btn)
        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn start post button. Screenshot: {screenshot}"
            }

        print("LinkedIn start post button clicked")

        # keep your remaining logic here...
        return {"success": True, "message": "Start post button clicked"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }