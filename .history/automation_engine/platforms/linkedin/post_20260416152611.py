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


def find_start_post_button(driver):
    # CSS selector attempts
    for selector in START_POST_SELECTORS:
        try:
            element = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5)
            print("Start post button found using CSS:", selector)
            return element
        except Exception:
            continue

    # XPath fallback attempts
    xpath_selectors = [
        "//button[contains(@aria-label, 'Start a post')]",
        "//button[contains(@aria-label, 'post')]",
        "//div[contains(@class, 'share-box-feed-entry__trigger')]",
        "//button[contains(@class, 'share-box-feed-entry__trigger')]",
        "//div[@role='button' and contains(@aria-label, 'post')]",
        "//span[contains(text(), 'Start a post')]/ancestor::button[1]",
        "//span[contains(text(), 'Start a post')]/ancestor::*[@role='button'][1]",
    ]

    for xpath in xpath_selectors:
        try:
            element = wait_for_clickable(driver, By.XPATH, xpath, timeout=5)
            print("Start post button found using XPath:", xpath)
            return element
        except Exception:
            continue

    # JavaScript DOM fallback
    try:
        js = """
        const candidates = Array.from(document.querySelectorAll('button, div[role="button"], span'));
        for (const el of candidates) {
            const text = (el.innerText || el.textContent || '').trim().toLowerCase();
            const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
            const cls = (el.className || '').toString().toLowerCase();

            if (
                aria.includes('start a post') ||
                text.includes('start a post') ||
                cls.includes('share-box-feed-entry__trigger')
            ) {
                return el;
            }
        }
        return null;
        """
        element = driver.execute_script(js)
        if element:
            print("Start post button found using JavaScript DOM search")
            return element
    except Exception as e:
        print("JavaScript fallback failed:", str(e))

    return None


def find_textbox(driver):
    for selector in TEXTBOX_SELECTORS:
        try:
            textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=5)
            print("Textbox found using:", selector)
            return textbox
        except Exception:
            continue

    xpath_selectors = [
        "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']",
        "//div[contains(@class,'ql-editor') and @contenteditable='true']",
        "//div[@contenteditable='true' and @role='textbox']",
        "//div[@contenteditable='true']",
    ]

    for xpath in xpath_selectors:
        try:
            textbox = wait_for_visible(driver, By.XPATH, xpath, timeout=5)
            print("Textbox found using XPath:", xpath)
            return textbox
        except Exception:
            continue

    return None


def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            post_button = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5)
            print("Post button found using:", selector)
            return post_button
        except Exception:
            continue

    xpath_selectors = [
        "//div[@role='dialog']//button[contains(@aria-label,'Post')]",
        "//button[contains(@class,'share-actions__primary-action')]",
        "//span[text()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_selectors:
        try:
            post_button = wait_for_clickable(driver, By.XPATH, xpath, timeout=5)
            print("Post button found using XPath:", xpath)
            return post_button
        except Exception:
            continue

    return None


def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)
        medium_pause()

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        start_post_button = find_start_post_button(driver)

        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, start_post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Start post clicked using JavaScript")
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
                return {
                    "success": False,
                    "message": f"Start post click failed. Screenshot: {screenshot}"
                }

        print("LinkedIn 'Start a post' button clicked")
        time.sleep(5)

        textbox = find_textbox(driver)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        safe_click(driver, textbox)
        print("Textbox clicked")

        type_like_human(textbox, post.caption)
        print("Caption typed")

        medium_pause()
        time.sleep(2)

        post_button = find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", post_button)
                print("Post button clicked using JavaScript")
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
                return {
                    "success": False,
                    "message": f"LinkedIn post button click failed. Screenshot: {screenshot}"
                }

        print("Post published on LinkedIn")
        medium_pause()

        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}