# automation_engine/platforms/linkedin/post.py

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.common.upload_helper import upload_file

from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    START_POST_XPATHS,
    TEXTBOX_SELECTORS,
    TEXTBOX_XPATHS,
    POST_BUTTON_SELECTORS,
    POST_BUTTON_XPATHS,
    MEDIA_UPLOAD_SELECTORS,
    MEDIA_UPLOAD_XPATHS,
)
from automation_engine.platforms.linkedin.utils import (
    scroll_to_top,
    dismiss_any_overlay,
    wait_for_feed,
)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _wait_clickable(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def _wait_present(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def _is_visible(element) -> bool:
    """Check whether an element is truly visible and not aria-hidden."""
    try:
        if not element.is_displayed():
            return False
        classes = (element.get_attribute("class") or "").lower()
        aria_hidden = (element.get_attribute("aria-hidden") or "").lower()
        if "hidden" in classes or aria_hidden == "true":
            return False
        return True
    except Exception:
        return False


def _safe_element_click(driver, element) -> bool:
    """
    Try multiple click strategies in order:
    1. safe_click (scroll + normal click / JS fallback)
    2. scroll + direct .click()
    3. pure JS click
    """
    try:
        if safe_click(driver, element):
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

    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        print(f"JS click failed: {e}")
        return False


def _find_first_clickable_css(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = _wait_clickable(driver, By.CSS_SELECTOR, selector, timeout)
            if _is_visible(element):
                print(f"[LinkedIn] CSS matched: {selector}")
                return element
        except Exception:
            continue
    return None


def _find_first_clickable_xpath(driver, xpaths, timeout=10):
    for xpath in xpaths:
        try:
            element = _wait_clickable(driver, By.XPATH, xpath, timeout)
            if _is_visible(element):
                print(f"[LinkedIn] XPath matched: {xpath}")
                return element
        except Exception:
            continue
    return None


# ─── Start Post button ────────────────────────────────────────────────────────

def _find_start_post_button(driver):
    """
    Locate the 'Start a post' button using CSS → XPath → JS DOM fallback.
    """
    btn = _find_first_clickable_css(driver, START_POST_SELECTORS)
    if btn:
        return btn

    btn = _find_first_clickable_xpath(driver, START_POST_XPATHS)
    if btn:
        return btn

    # JavaScript DOM walk as last resort
    print("[LinkedIn] CSS/XPath failed — trying JS DOM search for Start a post...")
    try:
        btn = driver.execute_script("""
            const candidates = document.querySelectorAll(
                'button, a, div[role="button"], div[tabindex], span, div'
            );

            function isVisible(el) {
                const s = window.getComputedStyle(el);
                return s.display !== 'none' &&
                       s.visibility !== 'hidden' &&
                       el.offsetParent !== null;
            }

            for (const el of candidates) {
                const text = (el.innerText || el.textContent || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                const placeholder = el.getAttribute('placeholder') ||
                                    el.getAttribute('aria-placeholder') || '';

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
                null
            );
        """)
        if btn:
            print("[LinkedIn] 'Start a post' button found via JS DOM search")
        return btn
    except Exception as e:
        print(f"[LinkedIn] JS start-post search failed: {e}")
        return None


# ─── Modal detection ──────────────────────────────────────────────────────────

def _wait_for_modal(driver, timeout=20):
    """
    Poll for the LinkedIn post composer modal.
    Skips video player dialogs and aria-hidden overlays.
    """
    print("[LinkedIn] Waiting for post composer modal...")
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], [aria-modal='true']")
            print(f"[LinkedIn] Dialogs found: {len(dialogs)}")

            for dialog in dialogs:
                try:
                    if not dialog.is_displayed():
                        continue

                    classes = (dialog.get_attribute("class") or "").lower()
                    aria_hidden = (dialog.get_attribute("aria-hidden") or "").lower()

                    # skip video / hidden overlays
                    if any(k in classes for k in ("vjs-", "video", "hidden")):
                        continue
                    if aria_hidden == "true":
                        continue

                    html = (dialog.get_attribute("outerHTML") or "")[:6000].lower()
                    keywords = ["start a post", "contenteditable", "textbox", "share", "editor"]

                    if any(kw in html for kw in keywords):
                        print("[LinkedIn] Composer modal detected.")
                        return dialog

                except Exception:
                    continue

        except Exception:
            pass

        time.sleep(1)

    print("[LinkedIn] No composer modal found within timeout.")
    return None


# ─── Textbox ──────────────────────────────────────────────────────────────────

def _find_textbox_in_context(driver, root=None):
    """
    Search for the post textbox within `root` element (modal) or the full page.
    Falls back to iframe detection and JS DOM walk.
    """
    search_root = root if root else driver

    # CSS selectors
    for selector in TEXTBOX_SELECTORS:
        try:
            elements = search_root.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if _is_visible(el):
                    print(f"[LinkedIn] Textbox found via CSS: {selector}")
                    return el
        except Exception:
            continue

    # XPath selectors
    for xpath in TEXTBOX_XPATHS:
        try:
            elements = search_root.find_elements(By.XPATH, xpath)
            for el in elements:
                if _is_visible(el):
                    print(f"[LinkedIn] Textbox found via XPath: {xpath}")
                    return el
        except Exception:
            continue

    # If we were scoped to modal, retry on full page
    if root is not None:
        print("[LinkedIn] Scoped search failed — retrying on full page...")
        result = _find_textbox_in_context(driver, root=None)
        if result:
            return result

    # iframe detection
    print("[LinkedIn] Trying iframe detection...")
    try:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(frame)
                candidates = driver.find_elements(
                    By.CSS_SELECTOR, "[role='textbox'], [contenteditable='true'], .ql-editor"
                )
                for el in candidates:
                    if _is_visible(el):
                        print("[LinkedIn] Textbox found inside iframe.")
                        return el
            except Exception:
                continue
        driver.switch_to.default_content()
    except Exception:
        pass

    # JavaScript DOM walk
    print("[LinkedIn] Trying JS DOM search for textbox...")
    try:
        textbox = driver.execute_script("""
            function isVisible(el) {
                const s = window.getComputedStyle(el);
                return s.display !== 'none' &&
                       s.visibility !== 'hidden' &&
                       el.offsetParent !== null &&
                       el.getAttribute('aria-hidden') !== 'true' &&
                       !(el.className || '').toString().toLowerCase().includes('hidden');
            }

            const selectors = [
                '[role="textbox"]',
                '[contenteditable="true"]',
                '[aria-multiline="true"]',
                '.ql-editor',
                'p[data-placeholder]'
            ];

            for (const sel of selectors) {
                for (const el of document.querySelectorAll(sel)) {
                    if (isVisible(el)) return el;
                }
            }
            return null;
        """)
        if textbox:
            print("[LinkedIn] Textbox found via JS DOM search.")
        return textbox
    except Exception as e:
        print(f"[LinkedIn] JS textbox search failed: {e}")
        return None


def _type_into_textbox(driver, textbox, text: str) -> bool:
    """
    Type text into the LinkedIn composer textbox using multiple fallback strategies.
    """
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
    time.sleep(1)
    _safe_element_click(driver, textbox)
    time.sleep(1)

    # Clear any existing content
    try:
        textbox.send_keys(Keys.CONTROL, "a")
        textbox.send_keys(Keys.BACKSPACE)
    except Exception:
        pass

    # Strategy 1: human-like typing
    try:
        type_like_human(textbox, text)
        print("[LinkedIn] Text typed via type_like_human.")
        return True
    except Exception as e:
        print(f"[LinkedIn] type_like_human failed: {e}")

    # Strategy 2: send_keys
    try:
        textbox.send_keys(text)
        print("[LinkedIn] Text typed via send_keys.")
        return True
    except Exception as e:
        print(f"[LinkedIn] send_keys failed: {e}")

    # Strategy 3: ActionChains
    try:
        ActionChains(driver).move_to_element(textbox).click().pause(1).send_keys(text).perform()
        print("[LinkedIn] Text typed via ActionChains.")
        return True
    except Exception as e:
        print(f"[LinkedIn] ActionChains failed: {e}")

    # Strategy 4: JavaScript injection
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
        print("[LinkedIn] Text inserted via JavaScript.")
        return True
    except Exception as e:
        print(f"[LinkedIn] JS text insertion failed: {e}")

    return False


# ─── Post button ──────────────────────────────────────────────────────────────

def _find_post_button(driver):
    """
    Locate the final 'Post' submit button using CSS → XPath → JS DOM fallback.
    """
    btn = _find_first_clickable_css(driver, POST_BUTTON_SELECTORS)
    if btn:
        return btn

    btn = _find_first_clickable_xpath(driver, POST_BUTTON_XPATHS)
    if btn:
        return btn

    print("[LinkedIn] CSS/XPath failed — trying JS DOM search for Post button...")
    try:
        btn = driver.execute_script("""
            function isVisible(el) {
                const s = window.getComputedStyle(el);
                return s.display !== 'none' &&
                       s.visibility !== 'hidden' &&
                       el.offsetParent !== null &&
                       el.getAttribute('aria-hidden') !== 'true' &&
                       !(el.className || '').toString().toLowerCase().includes('hidden');
            }

            for (const el of document.querySelectorAll('button, [role="button"]')) {
                const text = (el.innerText || el.textContent || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';

                if (!disabled && isVisible(el) && (text === 'Post' || aria === 'Post')) {
                    return el;
                }
            }
            return null;
        """)
        if btn:
            print("[LinkedIn] Post button found via JS DOM search.")
        return btn
    except Exception as e:
        print(f"[LinkedIn] JS post-button search failed: {e}")
        return None


# ─── Optional: media upload ───────────────────────────────────────────────────

def _attach_media(driver, image_path: str) -> bool:
    """
    Attach an image to the LinkedIn post composer (optional).
    Tries CSS selectors for the media upload button, then sends the file path.
    """
    media_btn = _find_first_clickable_css(driver, MEDIA_UPLOAD_SELECTORS)
    if not media_btn:
        media_btn = _find_first_clickable_xpath(driver, MEDIA_UPLOAD_XPATHS)

    if not media_btn:
        print("[LinkedIn] Media upload button not found.")
        return False

    _safe_element_click(driver, media_btn)
    time.sleep(2)

    try:
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_file(file_input, image_path)
        print(f"[LinkedIn] Media file attached: {image_path}")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"[LinkedIn] File upload failed: {e}")
        return False


# ─── Main entry point ─────────────────────────────────────────────────────────

def post_to_linkedin(driver, post) -> dict:
    """
    Publish a text post (with optional image) to LinkedIn.

    Args:
        driver: Selenium WebDriver instance (must already be logged in).
        post:   Django Post model instance with at least:
                    - post.caption  (str)
                    - post.image_path (str | None)  [optional]

    Returns:
        dict with keys:
            success (bool)
            message (str)
    """
    try:
        caption = getattr(post, "caption", None) or ""
        image_path = getattr(post, "image_path", None)

        if not caption.strip():
            return {"success": False, "message": "Caption is empty for LinkedIn post."}

        # ── 1. Navigate to feed ───────────────────────────────────────────────
        print("[LinkedIn] Navigating to LinkedIn feed...")
        driver.switch_to.default_content()
        driver.get("https://www.linkedin.com/feed/")
        medium_pause()
        time.sleep(6)

        scroll_to_top(driver)
        dismiss_any_overlay(driver)
        wait_for_feed(driver, timeout=20)

        # ── 2. Click 'Start a post' ───────────────────────────────────────────
        print("[LinkedIn] Looking for 'Start a post' button...")
        start_btn = _find_start_post_button(driver)

        if not start_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"'Start a post' button not found. Screenshot: {screenshot}",
            }

        if not _safe_element_click(driver, start_btn):
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Failed to click 'Start a post' button. Screenshot: {screenshot}",
            }

        print("[LinkedIn] 'Start a post' button clicked.")
        time.sleep(4)

        # ── 3. Wait for composer modal ────────────────────────────────────────
        modal = _wait_for_modal(driver, timeout=20)
        if not modal:
            screenshot = save_screenshot(driver, prefix="linkedin_modal_not_found")
            return {
                "success": False,
                "message": f"Composer modal did not appear. Screenshot: {screenshot}",
            }

        medium_pause()
        time.sleep(2)

        # ── 4. (Optional) attach image ────────────────────────────────────────
        if image_path:
            print(f"[LinkedIn] Attaching media: {image_path}")
            _attach_media(driver, image_path)

        # ── 5. Find & fill textbox ────────────────────────────────────────────
        textbox = _find_textbox_in_context(driver, root=modal)
        if not textbox:
            try:
                print("[LinkedIn] Modal HTML preview:")
                print((modal.get_attribute("outerHTML") or "")[:3000])
            except Exception:
                pass
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"Textbox not found inside composer. Screenshot: {screenshot}",
            }

        if not _type_into_textbox(driver, textbox, caption):
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Failed to type caption into textbox. Screenshot: {screenshot}",
            }

        print("[LinkedIn] Caption typed.")
        medium_pause()
        time.sleep(3)

        # ── 6. Click 'Post' button ────────────────────────────────────────────
        post_button = _find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"Post button not found. Screenshot: {screenshot}",
            }

        if not _safe_element_click(driver, post_button):
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"Failed to click Post button. Screenshot: {screenshot}",
            }

        print("[LinkedIn] Post button clicked.")
        time.sleep(6)

        # ── 7. Clean up & confirm ─────────────────────────────────────────────
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_success")
        return {
            "success": True,
            "message": f"Post published successfully on LinkedIn. Screenshot: {screenshot}",
        }

    except Exception as e:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}",
        }