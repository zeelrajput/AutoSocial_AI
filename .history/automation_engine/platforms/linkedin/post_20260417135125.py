import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


# ─────────────────────────────────────────────
# POPUP DISMISSAL
# ─────────────────────────────────────────────

def close_linkedin_popups(driver):
    popup_xpaths = [
        "//button[@aria-label='Dismiss']",
        "//button[@aria-label='Close']",
        "//button[contains(@class,'artdeco-modal__dismiss')]",
        "//button[.//span[normalize-space()='Not now']]",
        "//button[.//span[normalize-space()='Got it']]",
        "//button[.//span[normalize-space()='Skip']]",
    ]
    for xpath in popup_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        print("Closed popup using:", xpath)
                except Exception:
                    continue
        except Exception:
            continue


# ─────────────────────────────────────────────
# FIND "START A POST" BUTTON
# ─────────────────────────────────────────────

def find_start_post_button(driver):
    # 1. CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if not (el.is_displayed() and el.is_enabled()):
                        continue
                    text = (el.text or "").strip().lower()
                    aria = (el.get_attribute("aria-label") or "").strip().lower()
                    cls  = (el.get_attribute("class") or "").strip().lower()
                    if (
                        "start a post" in text
                        or "start a post" in aria
                        or "share-box-feed-entry__trigger" in cls
                        or "share-box-feed-entry--closed" in cls
                    ):
                        print("Start post button found using CSS:", selector)
                        print("Button text:", el.text)
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # 2. XPath fallback
    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and @aria-label='Start a post']",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
        "//div[contains(normalize-space(),'Start a post') and @role='button']",
        "//button[contains(., 'Start a post')]",
        "//div[@role='button'][.//span[contains(., 'Start a post')]]",
    ]
    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"Checking xpath: {xpath} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        print("Button text:", el.text)
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # 3. JavaScript fallback
    try:
        js_element = driver.execute_script("""
            const candidates = Array.from(
                document.querySelectorAll('button, div[role="button"], a')
            );
            return candidates.find(el => {
                const text  = (el.innerText || el.textContent || '').trim().toLowerCase();
                const aria  = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const cls   = (el.className || '').toString().toLowerCase();
                const visible = !!(
                    el.offsetWidth || el.offsetHeight || el.getClientRects().length
                );
                if (!visible) return false;
                return (
                    text.includes('start a post') ||
                    aria.includes('start a post') ||
                    cls.includes('share-box-feed-entry__trigger') ||
                    cls.includes('share-box-feed-entry--closed')
                );
            }) || null;
        """)
        if js_element:
            print("Start post button found using JavaScript fallback")
            return js_element
    except Exception as e:
        print("JavaScript fallback failed:", str(e))

    return None


# ─────────────────────────────────────────────
# CLICK "START A POST" (React-compatible)
# ─────────────────────────────────────────────

def click_start_post_button(driver, button):
    """
    Fires mousedown + mouseup + click as React synthetic events,
    then falls back to a plain .click() so the composer actually opens.
    """
    try:
        driver.execute_script("""
            const el = arguments[0];
            el.scrollIntoView({block: 'center'});
            ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                el.dispatchEvent(new MouseEvent(eventType, {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
            });
        """, button)
        print("Dispatched React-compatible click events")
    except Exception as e:
        print("React click dispatch failed:", e)

    # Always also try a normal click as a backup
    try:
        button.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", button)
            print("Start post clicked using JavaScript fallback")
        except Exception as e:
            print("All click strategies failed:", e)
            return False

    return True


# ─────────────────────────────────────────────
# WAIT FOR COMPOSER / TEXTBOX  (v2 — smart polling)
# ─────────────────────────────────────────────

def wait_for_linkedin_composer_v2(driver, timeout=20):
    """
    Polls for the composer textbox using multiple strategies.
    Returns the textbox WebElement, or None on timeout.
    """
    COMPOSER_SELECTORS = [
        # Standard modal dialog
        (By.CSS_SELECTOR, "div[role='dialog'] div[contenteditable='true']"),
        (By.CSS_SELECTOR, "div[role='dialog'] div.ql-editor"),
        (By.CSS_SELECTOR, "div[role='dialog'] div[role='textbox']"),
        # Inline / no-modal editor
        (By.CSS_SELECTOR, "div.ql-editor[contenteditable='true']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][data-placeholder]"),
        (By.CSS_SELECTOR, "div[role='textbox']"),
        # Overlay / drawer style
        (By.CSS_SELECTOR, "div.share-creation-state__placeholder"),
        (By.XPATH,        "//*[@data-placeholder and @contenteditable='true']"),
        (By.XPATH,        "//*[contains(@data-placeholder,'talk about')]"),
        (By.XPATH,        "//*[contains(@data-placeholder,'share')]"),
        (By.XPATH,        "//*[contains(@data-placeholder,'Write')]"),
        # Aria-based
        (By.CSS_SELECTOR, "[aria-label='Text editor for creating content']"),
        (By.XPATH,        "//div[@aria-label and @contenteditable='true']"),
    ]

    print("Waiting for LinkedIn composer to appear...")
    end_time = time.time() + timeout
    attempt  = 0

    while time.time() < end_time:
        attempt += 1
        print(f"Composer wait attempt #{attempt} ({int(end_time - time.time())}s left)")

        for by, selector in COMPOSER_SELECTORS:
            try:
                elements = driver.find_elements(by, selector)
                for el in elements:
                    try:
                        if el.is_displayed():
                            print(f"✅ Composer found: [{by}] {selector}")
                            print(
                                f"   tag={el.tag_name}, "
                                f"role={el.get_attribute('role')}, "
                                f"ce={el.get_attribute('contenteditable')}, "
                                f"class="
                                f"{(el.get_attribute('class') or '')[:60]}"
                            )
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # JS bounding-rect check for any visible contenteditable
        try:
            js_editor = driver.execute_script("""
                return Array.from(
                    document.querySelectorAll('[contenteditable="true"]')
                ).find(el => {
                    if (!el.offsetParent) return false;
                    const rect = el.getBoundingClientRect();
                    return rect.width > 50 && rect.height > 20;
                }) || null;
            """)
            if js_editor:
                print("✅ Composer found via JS bounding-rect check")
                return js_editor
        except Exception:
            pass

        time.sleep(0.8)

    print("❌ Composer not found after timeout")
    return None


# ─────────────────────────────────────────────
# TYPE INTO EDITOR
# ─────────────────────────────────────────────

def type_into_linkedin_editor(driver, textbox, text):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", textbox
        )
        time.sleep(1)

        # Click to focus
        try:
            safe_click(driver, textbox)
        except Exception:
            try:
                textbox.click()
            except Exception:
                driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)

        # Switch to active element in case we landed on a placeholder wrapper
        try:
            active = driver.switch_to.active_element
            if active and active.is_displayed():
                textbox = active
                print("Using active element as textbox")
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        time.sleep(0.5)

        # Clear existing content
        try:
            textbox.send_keys(Keys.CONTROL + "a")
            textbox.send_keys(Keys.DELETE)
            time.sleep(0.3)
        except Exception:
            pass

        # Strategy 1 — send_keys char by char (most reliable for LinkedIn)
        try:
            for ch in text:
                textbox.send_keys(ch)
                time.sleep(0.03)
            print("Caption typed using send_keys")
            return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # Strategy 2 — ActionChains
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver)\
                .move_to_element(textbox)\
                .click()\
                .pause(0.5)\
                .send_keys(text)\
                .perform()
            print("Caption typed using ActionChains")
            return True
        except Exception as e:
            print("ActionChains failed:", str(e))

        # Strategy 3 — JavaScript
        try:
            driver.execute_script("""
                const el   = arguments[0];
                const text = arguments[1];
                el.click();
                el.focus();
                if (document.activeElement && document.activeElement !== el) {
                    document.activeElement.focus();
                }
                const target = document.activeElement || el;
                if ('value' in target) {
                    target.value = text;
                    target.dispatchEvent(new Event('input',  { bubbles: true }));
                    target.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                target.innerHTML  = '';
                target.textContent = text;
                target.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    data: text,
                    inputType: 'insertText'
                }));
                return true;
            """, textbox, text)
            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_linkedin_editor error:", str(e))
        return False


# ─────────────────────────────────────────────
# FIND "POST" BUTTON
# ─────────────────────────────────────────────

def find_post_button(driver, dialog=None):
    search_root = dialog if dialog is not None else driver

    for selector in POST_BUTTON_SELECTORS:
        try:
            local_selector = selector.replace("div[role='dialog'] ", "")
            elements = search_root.find_elements(By.CSS_SELECTOR, local_selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using CSS:", selector)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        ".//button[contains(@class,'share-actions__primary-action')]",
        ".//button[@aria-label='Post']",
        ".//button[contains(@aria-label,'Post')]",
        ".//span[normalize-space()='Post']/ancestor::button[1]",
        "//button[contains(., 'Post')]",
    ]
    for xpath in xpath_candidates:
        try:
            elements = search_root.find_elements(By.XPATH, xpath)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using XPath:", xpath)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    return None


# ─────────────────────────────────────────────
# DEBUG HELPER  (remove after confirming flow)
# ─────────────────────────────────────────────

def dump_dom_snapshot(driver, label="dom_snapshot"):
    try:
        html = driver.execute_script("return document.documentElement.outerHTML;")
        path = f"screenshots/{label}_{int(time.time())}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"DOM snapshot saved: {path}")
    except Exception as e:
        print("DOM snapshot failed:", e)


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(10)
        medium_pause()

        try:
            driver.refresh()
            print("LinkedIn feed page refreshed")
            time.sleep(6)
        except Exception:
            pass

        medium_pause()

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        try:
            body_preview = driver.execute_script(
                "return document.body.innerText.slice(0, 2000);"
            )
            print("Page text preview:", body_preview)
        except Exception:
            pass

        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception:
            pass

        close_linkedin_popups(driver)

        # ── Step 1: Find "Start a post" ──────────────────────────────────
        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        # ── Step 2: Click it (React-compatible) ──────────────────────────
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                start_post_button
            )
            time.sleep(1)

            clicked = click_start_post_button(driver, start_post_button)
            if not clicked:
                screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
                return {
                    "success": False,
                    "message": f"Start post click failed. Screenshot: {screenshot}"
                }

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        time.sleep(2)

        # ── Debug: save DOM right after click ────────────────────────────
        # Remove this line once the composer is reliably detected
        dump_dom_snapshot(driver, "after_start_post_click")

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        # ── Step 3: Wait for composer (smart polling, no static sleep) ───
        textbox = wait_for_linkedin_composer_v2(driver, timeout=20)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": (
                    "LinkedIn composer opened visually but textbox was not detected. "
                    f"Screenshot: {screenshot}"
                )
            }

        # Find parent dialog for scoping the Post button later
        dialog = None
        try:
            dialog = driver.execute_script("""
                let node = arguments[0];
                while (node) {
                    if (
                        node.getAttribute &&
                        node.getAttribute('role') === 'dialog'
                    ) return node;
                    node = node.parentElement;
                }
                return null;
            """, textbox)
        except Exception:
            pass

        try:
            outer_html = driver.execute_script(
                "return arguments[0].outerHTML;", textbox
            )
            print("Textbox outerHTML:", outer_html[:1000] if outer_html else "None")
        except Exception:
            pass

        # ── Step 4: Type caption ─────────────────────────────────────────
        typed = type_into_linkedin_editor(driver, textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        # ── Step 5: Find and click Post button ───────────────────────────
        post_button = find_post_button(driver, dialog=dialog)
        if not post_button:
            post_button = find_post_button(driver)   # global fallback

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                post_button
            )
            time.sleep(1)

            clicked = safe_click(driver, post_button)
            if not clicked:
                try:
                    post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", post_button)
                    print("Post button clicked using JavaScript")

            print("Post published on LinkedIn")
            medium_pause()

            return {
                "success": True,
                "message": "Post published on LinkedIn"
            }

        except Exception as e:
            screenshot = save_screenshot(
                driver, prefix="linkedin_post_button_click_failed"
            )
            return {
                "success": False,
                "message": (
                    f"LinkedIn post button click failed: {str(e)}. "
                    f"Screenshot: {screenshot}"
                )
            }

    except Exception as e:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }