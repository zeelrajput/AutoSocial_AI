import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _wait_clickable(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def _wait_present(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def _is_visible(element):
    try:
        if not element.is_displayed():
            return False

        classes = (element.get_attribute("class") or "").lower()
        aria_hidden = (element.get_attribute("aria-hidden") or "").lower()

        if "hidden" in classes:
            return False
        if aria_hidden == "true":
            return False

        return True
    except Exception:
        return False


def _find_first_clickable_css(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = _wait_clickable(driver, By.CSS_SELECTOR, selector, timeout)
            if _is_visible(element):
                print(f"LinkedIn clickable CSS matched: {selector}")
                return element
        except Exception:
            continue
    return None


def _find_first_clickable_xpath(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = _wait_clickable(driver, By.XPATH, selector, timeout)
            if _is_visible(element):
                print(f"LinkedIn clickable XPath matched: {selector}")
                return element
        except Exception:
            continue
    return None


def _js_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.7)
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        print(f"JS click failed: {e}")
        return False


def _safe_element_click(driver, element):
    try:
        result = safe_click(driver, element)
        if result:
            return True
    except Exception as e:
        print(f"safe_click failed: {e}")

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.7)
        element.click()
        return True
    except Exception as e:
        print(f"element.click failed: {e}")

    return _js_click(driver, element)


def _find_start_post_via_js(driver):
    try:
        element = driver.execute_script("""
            const allElements = document.querySelectorAll(
                'button, a, div[role="button"], div[tabindex], span, div'
            );

            function isVisible(el) {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       el.offsetParent !== null;
            }

            for (const el of allElements) {
                const text = (el.innerText || el.textContent || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                const placeholder = el.getAttribute('placeholder') || el.getAttribute('aria-placeholder') || '';

                if (!isVisible(el)) continue;

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

            return (
                document.querySelector('button.share-box-feed-entry__trigger') ||
                document.querySelector('div.share-box-feed-entry__top-bar button') ||
                document.querySelector('a[href*="/post/new/"]') ||
                document.querySelector('a[href*="create-post"]') ||
                null
            );
        """)
        if element:
            print("LinkedIn create/start post trigger found via JavaScript DOM search")
        return element
    except Exception as e:
        print(f"JS start-post search failed: {e}")
        return None


def _wait_for_modal(driver, timeout=15):
    print("Waiting for LinkedIn post composer modal...")

    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']")

            for i, dialog in enumerate(dialogs, start=1):
                try:
                    if not dialog.is_displayed():
                        continue

                    classes = (dialog.get_attribute("class") or "").lower()
                    aria_hidden = (dialog.get_attribute("aria-hidden") or "").lower()
                    html = (dialog.get_attribute("outerHTML") or "")[:5000].lower()

                    if "vjs-" in classes:
                        continue
                    if "video" in classes:
                        continue
                    if "hidden" in classes:
                        continue
                    if aria_hidden == "true":
                        continue

                    keywords = [
                        "create a post",
                        "start a post",
                        "contenteditable",
                        "textbox",
                        "share",
                        "post",
                    ]

                    if any(keyword in html for keyword in keywords):
                        print(f"Real LinkedIn modal detected at index {i}")
                        return dialog

                except Exception:
                    continue

        except Exception:
            pass

        time.sleep(1)

    print("No valid LinkedIn composer modal found")
    return None


def _find_textbox_in_modal(driver, modal):
    print("Finding LinkedIn textbox inside modal...")

    # CSS
    for selector in TEXTBOX_SELECTORS:
        try:
            elements = modal.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if _is_visible(el):
                    print(f"LinkedIn textbox matched via CSS: {selector}")
                    return el
        except Exception:
            continue

    # XPath
    for selector in TEXTBOX_XPATHS:
        try:
            elements = modal.find_elements(By.XPATH, selector)
            for el in elements:
                if _is_visible(el):
                    print(f"LinkedIn textbox matched via XPath: {selector}")
                    return el
        except Exception:
            continue

    # JS fallback
    print("CSS/XPath textbox search failed — trying JavaScript DOM search...")
    try:
        textbox = driver.execute_script("""
            const dialogs = document.querySelectorAll('[role="dialog"], [aria-modal="true"]');

            function isVisible(el) {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       el.offsetParent !== null &&
                       el.getAttribute('aria-hidden') !== 'true' &&
                       !(el.className || '').toString().toLowerCase().includes('hidden');
            }

            for (const modal of dialogs) {
                if (!isVisible(modal)) continue;

                const modalHtml = (modal.outerHTML || '').toLowerCase();

                if (
                    modalHtml.includes('create a post') ||
                    modalHtml.includes('start a post') ||
                    modalHtml.includes('contenteditable') ||
                    modalHtml.includes('textbox') ||
                    modalHtml.includes('share')
                ) {
                    const selectors = [
                        '[role="textbox"]',
                        '[contenteditable="true"]',
                        '[aria-multiline="true"]',
                        '.ql-editor',
                        'p[data-placeholder]'
                    ];

                    for (const sel of selectors) {
                        const nodes = modal.querySelectorAll(sel);
                        for (const el of nodes) {
                            if (isVisible(el)) return el;
                        }
                    }
                }
            }

            return null;
        """)
        if textbox:
            print("LinkedIn textbox found via JavaScript DOM search")
        return textbox
    except Exception as e:
        print(f"JS textbox search failed: {e}")
        return None


def _type_into_textbox(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        time.sleep(0.8)
        _safe_element_click(driver, textbox)
        time.sleep(0.8)

        try:
            textbox.send_keys(Keys.CONTROL, "a")
            textbox.send_keys(Keys.BACKSPACE)
        except Exception:
            pass

        try:
            type_like_human(textbox, text)
            print("Text typed via type_like_human")
            return True
        except Exception as e:
            print(f"type_like_human failed: {e}")

        textbox.send_keys(text)
        print("Text typed via send_keys")
        return True

    except Exception as e:
        print(f"Direct typing failed: {e}")

    try:
        ActionChains(driver).move_to_element(textbox).click().pause(1).send_keys(text).perform()
        print("Text typed via ActionChains")
        return True
    except Exception as e:
        print(f"ActionChains typing failed: {e}")

    try:
        driver.execute_script("""
            arguments[0].focus();

            if ('innerText' in arguments[0]) {
                arguments[0].innerText = arguments[1];
            } else if ('value' in arguments[0]) {
                arguments[0].value = arguments[1];
            }

            arguments[0].dispatchEvent(new InputEvent('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        """, textbox, text)
        print("Text inserted via JavaScript")
        return True
    except Exception as e:
        print(f"JS text insertion failed: {e}")

    return False


def _find_post_button(driver):
    print("Finding LinkedIn post button...")

    post_button = _find_first_clickable_css(driver, POST_BUTTON_SELECTORS, timeout=10)
    if post_button:
        return post_button

    post_button = _find_first_clickable_xpath(driver, POST_BUTTON_XPATHS, timeout=10)
    if post_button:
        return post_button

    try:
        post_button = driver.execute_script("""
            const dialogs = document.querySelectorAll('[role="dialog"], [aria-modal="true"]');

            function isVisible(el) {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       el.offsetParent !== null &&
                       el.getAttribute('aria-hidden') !== 'true' &&
                       !(el.className || '').toString().toLowerCase().includes('hidden');
            }

            for (const modal of dialogs) {
                if (!isVisible(modal)) continue;

                const modalHtml = (modal.outerHTML || '').toLowerCase();

                if (
                    modalHtml.includes('create a post') ||
                    modalHtml.includes('start a post') ||
                    modalHtml.includes('contenteditable') ||
                    modalHtml.includes('textbox') ||
                    modalHtml.includes('share')
                ) {
                    const candidates = modal.querySelectorAll('button, [role="button"]');

                    for (const el of candidates) {
                        const text = (el.innerText || el.textContent || '').trim();
                        const aria = el.getAttribute('aria-label') || '';
                        const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';

                        if (!disabled && isVisible(el) && (text === 'Post' || aria === 'Post')) {
                            return el;
                        }
                    }
                }
            }

            return null;
        """)
        if post_button:
            print("LinkedIn post button found via JavaScript DOM search")
        return post_button
    except Exception as e:
        print(f"JS post-button search failed: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def post_to_linkedin(driver, post):
    """
    post.caption is required
    Returns:
        {"success": bool, "message": str}
    """
    try:
        caption = getattr(post, "caption", None) or ""
        if not caption.strip():
            return {"success": False, "message": "Caption is empty for LinkedIn post."}

        print("Opening LinkedIn feed page...")
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(5)

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
        except Exception:
            pass

        time.sleep(2)

        print("Finding 'Start a post' button...")

        start_post_btn = _find_first_clickable_css(driver, START_POST_SELECTORS, timeout=8)
        if not start_post_btn:
            start_post_btn = _find_first_clickable_xpath(driver, START_POST_XPATHS, timeout=8)
        if not start_post_btn:
            print("CSS/XPath failed — trying JavaScript DOM search...")
            start_post_btn = _find_start_post_via_js(driver)

        if not start_post_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_not_found")
            return {
                "success": False,
                "message": f"LinkedIn 'Start a post' button not found. Screenshot: {screenshot}"
            }

        if not _safe_element_click(driver, start_post_btn):
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn 'Start a post' button. Screenshot: {screenshot}"
            }

        print("LinkedIn 'Start a post' button clicked")
        time.sleep(3)

        modal = _wait_for_modal(driver, timeout=15)
        if not modal:
            screenshot = save_screenshot(driver, prefix="linkedin_modal_not_found")
            return {
                "success": False,
                "message": f"LinkedIn modal not found. Screenshot: {screenshot}"
            }

        medium_pause()
        time.sleep(2)

        textbox = _find_textbox_in_modal(driver, modal)
        if not textbox:
            try:
                print("Modal HTML preview:")
                print((modal.get_attribute("outerHTML") or "")[:4000])
            except Exception:
                pass

            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        if not _type_into_textbox(driver, textbox, caption):
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Failed to type caption into LinkedIn textbox. Screenshot: {screenshot}"
            }

        print("LinkedIn caption typed")
        medium_pause()
        time.sleep(2)

        post_button = _find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn Post button not found. Screenshot: {screenshot}"
            }

        if not _safe_element_click(driver, post_button):
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"Failed to click LinkedIn Post button. Screenshot: {screenshot}"
            }

        print("LinkedIn Post button clicked")
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