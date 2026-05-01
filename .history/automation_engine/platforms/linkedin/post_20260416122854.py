import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.wait_helper import wait_for_clickable, wait_for_visible
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    START_POST_XPATHS,
    TEXTBOX_SELECTORS,
    TEXTBOX_XPATHS,
    POST_BUTTON_SELECTORS,
    POST_BUTTON_XPATHS,
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


def _find_first_visible_css(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            print(f"LinkedIn visible CSS matched: {selector}")
            return element
        except Exception:
            continue
    return None


def _find_first_visible_xpath(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = wait_for_visible(driver, By.XPATH, selector, timeout=timeout)
            print(f"LinkedIn visible XPath matched: {selector}")
            return element
        except Exception:
            continue
    return None


def _js_click(driver, element):
    """Fallback JavaScript click for elements that resist normal clicks."""
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        print(f"JS click failed: {e}")
        return False


def _find_start_post_via_js(driver):
    """
    Use JavaScript to find the 'Start a post' button directly in the DOM.
    This bypasses Selenium selector issues with dynamic/obfuscated class names.
    """
    try:
        element = driver.execute_script("""
            // Search all interactive elements for 'Start a post' text
            const allElements = document.querySelectorAll('button, div[role="button"], div[tabindex], span, div');
            for (let el of allElements) {
                const text = (el.innerText || el.textContent || '').trim();
                const placeholder = el.getAttribute('placeholder') || el.getAttribute('aria-placeholder') || '';
                if (text === 'Start a post' || placeholder.includes('Start a post')) {
                    return el;
                }
            }
            // Try placeholder attributes
            const byPlaceholder = document.querySelector('[placeholder*="post"], [aria-placeholder*="post"]');
            if (byPlaceholder) return byPlaceholder;

            // Try known share-box class patterns
            const shareBtn = document.querySelector(
                'button.share-box-feed-entry__trigger, ' +
                'div.share-box-feed-entry__trigger-container button, ' +
                'div.share-box-feed-entry__top-bar button'
            );
            if (shareBtn) return shareBtn;

            return null;
        """)
        if element:
            print("LinkedIn 'Start a post' button found via JavaScript DOM search")
        return element
    except Exception as e:
        print(f"JS DOM search failed: {e}")
        return None


def post_to_linkedin(driver, post):
    try:
        # Navigate to /feed/ where the "Start a post" button exists
        print("Opening LinkedIn feed page...")
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(6)

        # Scroll to top to ensure post box is visible
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Wait for page main content to render
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except Exception:
            pass
        time.sleep(2)

        print("Finding 'Start a post' button...")

        # Step 1: Try CSS selectors
        start_post_btn = _find_first_clickable_css(driver, START_POST_SELECTORS, timeout=10)

        # Step 2: Try XPath selectors
        if not start_post_btn:
            start_post_btn = _find_first_clickable_xpath(driver, START_POST_XPATHS, timeout=10)

        # Step 3: JavaScript DOM search — handles dynamic/obfuscated class names
        if not start_post_btn:
            print("CSS/XPath failed — trying JavaScript DOM search...")
            start_post_btn = _find_start_post_via_js(driver)

        if not start_post_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_not_found")
            return {
                "success": False,
                "message": f"LinkedIn create post button not found. Screenshot: {screenshot}"
            }

        # Try normal click, fall back to JS click
        clicked = safe_click(driver, start_post_btn)
        if not clicked:
            print("Normal click failed, trying JS click...")
            clicked = _js_click(driver, start_post_btn)

        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn create post button. Screenshot: {screenshot}"
            }

        print("LinkedIn 'Start a post' button clicked")
        medium_pause()
        time.sleep(4)

        print("Finding LinkedIn textbox...")
        textbox = _find_first_visible_css(driver, TEXTBOX_SELECTORS, timeout=15)

        if not textbox:
            textbox = _find_first_visible_xpath(driver, TEXTBOX_XPATHS, timeout=10)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, textbox)
        if not clicked:
            _js_click(driver, textbox)
        print("LinkedIn textbox clicked")

        type_like_human(textbox, post.caption)
        print("LinkedIn caption typed")

        medium_pause()
        time.sleep(2)

        print("Finding LinkedIn post button...")
        post_button = _find_first_clickable_css(driver, POST_BUTTON_SELECTORS, timeout=15)

        if not post_button:
            post_button = _find_first_clickable_xpath(driver, POST_BUTTON_XPATHS, timeout=10)

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, post_button)
        if not clicked:
            print("Normal click failed on post button, trying JS click...")
            clicked = _js_click(driver, post_button)

        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn post button. Screenshot: {screenshot}"
            }

        print("LinkedIn post button clicked")
        time.sleep(5)

        screenshot = save_screenshot(driver, prefix="linkedin_post_success")
        return {
            "success": True,
            "message": f"Post published on LinkedIn. Screenshot: {screenshot}"
        }

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }