import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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


# ─── Selector helpers ─────────────────────────────────────────────────────────

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


# ─── JavaScript helpers ───────────────────────────────────────────────────────

def _js_click(driver, element):
    """Fallback JavaScript click for elements that resist normal clicks."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        print(f"JS click failed: {e}")
        return False


def _find_start_post_via_js(driver):
    try:
        element = driver.execute_script("""
            const allElements = document.querySelectorAll(
                'button, a, div[role="button"], div[tabindex], span, div'
            );

            for (let el of allElements) {
                const text = (el.innerText || el.textContent || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                const placeholder = el.getAttribute('placeholder') || el.getAttribute('aria-placeholder') || '';

                if (
                    text.includes('Create a post') ||
                    text.includes('Start a post') ||
                    aria.includes('Create a post') ||
                    aria.includes('Start a post') ||
                    placeholder.includes('Create a post') ||
                    placeholder.includes('Start a post')
                ) {
                    return el;
                }
            }

            const byKnownLink = document.querySelector(
                'a[href*="/post/new/"], a[href*="create-post"]'
            );
            if (byKnownLink) return byKnownLink;

            const byKnownButton = document.querySelector(
                'button.share-box-feed-entry__trigger, ' +
                'div.share-box-feed-entry__top-bar button, ' +
                'div.share-creation-state button, ' +
                'div.share-box-v2 button'
            );
            if (byKnownButton) return byKnownButton;

            return null;
        """)
        if element:
            print("LinkedIn create/start post trigger found via JavaScript DOM search")
        return element
    except Exception as e:
        print(f"JS DOM search failed: {e}")
        return None


def _find_textbox_via_js(driver):
    """
    Use JavaScript to find the post composer textbox inside the modal.
    Runs after 'Start a post' is clicked and modal is open.
    """
    try:
        element = driver.execute_script("""
            // Look inside any open modal/dialog first
            const modal = document.querySelector(
                'div[role="dialog"], div[aria-modal="true"], ' +
                'div.share-creation-state, div.share-box-v2'
            );
            const scope = modal || document;

            // Priority order: role=textbox > ql-editor > contenteditable
            const textbox = (
                scope.querySelector('div[role="textbox"][contenteditable="true"]') ||
                scope.querySelector('div.ql-editor[contenteditable="true"]') ||
                scope.querySelector('div[contenteditable="true"][aria-multiline="true"]') ||
                scope.querySelector('div[contenteditable="true"]')
            );
            return textbox || null;
        """)
        if element:
            print("LinkedIn textbox found via JavaScript DOM search")
        return element
    except Exception as e:
        print(f"JS textbox search failed: {e}")
        return None


def _type_into_textbox(driver, textbox, text):
    """
    Type text into the LinkedIn composer textbox.
    Tries multiple methods: type_like_human → ActionChains → JS innerHTML → clipboard paste.
    """
    # Method 1: Use project's human typing helper
    try:
        safe_click(driver, textbox)
        time.sleep(0.5)
        type_like_human(textbox, text)
        print("Text typed via type_like_human")
        return True
    except Exception as e:
        print(f"type_like_human failed: {e}")

    # Method 2: ActionChains send_keys
    try:
        ActionChains(driver).move_to_element(textbox).click().send_keys(text).perform()
        print("Text typed via ActionChains")
        return True
    except Exception as e:
        print(f"ActionChains typing failed: {e}")

    # Method 3: Direct send_keys on element
    try:
        textbox.click()
        textbox.send_keys(text)
        print("Text typed via element.send_keys")
        return True
    except Exception as e:
        print(f"send_keys failed: {e}")

    # Method 4: JavaScript clipboard simulation (paste approach)
    try:
        driver.execute_script("""
            arguments[0].focus();
            arguments[0].click();

            // Dispatch an input event with the text
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLElement.prototype, 'innerText'
            );
            arguments[0].innerText = arguments[1];

            // Trigger input and change events so React/Vue state updates
            ['input', 'change', 'keyup', 'keydown'].forEach(eventType => {
                arguments[0].dispatchEvent(new Event(eventType, { bubbles: true }));
            });
        """, textbox, text)
        print("Text inserted via JavaScript innerHTML + events")
        return True
    except Exception as e:
        print(f"JS text insertion failed: {e}")

    return False


def _wait_for_modal(driver, timeout=15):
    modal_selectors = [
        "div[role='dialog']",
        "div[aria-modal='true']",
        "div.share-creation-state",
        "div.share-box-v2",
        "div.share-modal",
        "div.share-creation-state__main-editor",
    ]

    print("Waiting for LinkedIn post composer modal...")
    for selector in modal_selectors:
        try:
            modal = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            print(f"Modal detected via: {selector}")
            return modal
        except Exception:
            continue

    print("Modal wait timed out")
    return None


# ─── Main posting function ────────────────────────────────────────────────────

def post_to_linkedin(driver, post):
    """
    Post content to LinkedIn using Selenium automation.

    Steps:
    1. Navigate to LinkedIn feed
    2. Click 'Start a post' button
    3. Wait for composer modal to load
    4. Find and click the textbox
    5. Type the caption
    6. Click the Post button

    Args:
        driver: Selenium WebDriver instance (already logged in)
        post: Post object with `.caption` attribute

    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        # ── Step 1: Navigate to feed ──────────────────────────────────────────
        print("Opening LinkedIn feed page...")
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(6)

        # Scroll to top so the post box is in view
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Wait for main content to render
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except Exception:
            pass
        time.sleep(2)

        # ── Step 2: Find & click 'Start a post' ──────────────────────────────
        print("Finding 'Start a post' button...")

        # Step 2a: CSS selectors
        start_post_btn = _find_first_clickable_css(driver, START_POST_SELECTORS, timeout=10)

        # Step 2b: XPath selectors
        if not start_post_btn:
            start_post_btn = _find_first_clickable_xpath(driver, START_POST_XPATHS, timeout=10)

        # Step 2c: JavaScript DOM search (handles dynamic/obfuscated class names)
        if not start_post_btn:
            print("CSS/XPath failed — trying JavaScript DOM search...")
            start_post_btn = _find_start_post_via_js(driver)

        if not start_post_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_not_found")
            return {
                "success": False,
                "message": f"LinkedIn 'Start a post' button not found. Screenshot: {screenshot}"
            }

        # Click it — try normal click, then JS click
        clicked = safe_click(driver, start_post_btn)
        if not clicked:
            print("Normal click failed, trying JS click...")
            clicked = _js_click(driver, start_post_btn)

        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn 'Start a post' button. Screenshot: {screenshot}"
            }

        print("LinkedIn 'Start a post' button clicked")

        # ── Step 3: Wait for composer modal to fully load ─────────────────────
        _wait_for_modal(driver, timeout=15)

        # Extra buffer for modal animation + React rendering
        medium_pause()
        time.sleep(3)

        # ── Step 4: Find the textbox ──────────────────────────────────────────
        print("Finding LinkedIn textbox...")

        # Step 4a: CSS selectors (scoped to modal first)
        textbox = _find_first_visible_css(driver, TEXTBOX_SELECTORS, timeout=15)

        # Step 4b: XPath selectors
        if not textbox:
            textbox = _find_first_visible_xpath(driver, TEXTBOX_XPATHS, timeout=10)

        # Step 4c: JavaScript DOM search inside modal
        if not textbox:
            print("CSS/XPath textbox search failed — trying JavaScript DOM search...")
            textbox = _find_textbox_via_js(driver)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        # ── Step 5: Type the caption ──────────────────────────────────────────
        typed = _type_into_textbox(driver, textbox, post.caption)

        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Failed to type caption into LinkedIn textbox. Screenshot: {screenshot}"
            }

        print("LinkedIn caption typed")
        medium_pause()
        time.sleep(2)

        # ── Step 6: Find & click the Post button ──────────────────────────────
        print("Finding LinkedIn post button...")

        # Step 6a: CSS selectors
        post_button = _find_first_clickable_css(driver, POST_BUTTON_SELECTORS, timeout=15)

        # Step 6b: XPath selectors
        if not post_button:
            post_button = _find_first_clickable_xpath(driver, POST_BUTTON_XPATHS, timeout=10)

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn Post button not found. Screenshot: {screenshot}"
            }

        # Click post button
        clicked = safe_click(driver, post_button)
        if not clicked:
            print("Normal click failed on Post button, trying JS click...")
            clicked = _js_click(driver, post_button)

        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn Post button. Screenshot: {screenshot}"
            }

        print("LinkedIn Post button clicked")

        # Wait for post to be submitted
        time.sleep(5)

        screenshot = save_screenshot(driver, prefix="linkedin_post_success")
        return {
            "success": True,
            "message": f"Post published successfully on LinkedIn. Screenshot: {screenshot}"
        }

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }