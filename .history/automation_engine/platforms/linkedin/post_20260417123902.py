import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)


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


def find_start_post_button(driver):
    # 1. CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        text = (el.text or "").strip().lower()
                        aria = (el.get_attribute("aria-label") or "").strip().lower()
                        cls = (el.get_attribute("class") or "").strip().lower()

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
            const candidates = Array.from(document.querySelectorAll('button, div[role="button"], a'));
            return candidates.find(el => {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();

                const visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
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


def find_visible_dialog(driver):
    css_candidates = [
        "div[role='dialog']",
        "div.artdeco-modal",
        "section[aria-label*='Create a post']",
        "div.share-box_actions",
        "div.share-box-v2",
        "div.ql-container",
        "div.editor-content",
    ]

    for selector in css_candidates:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking dialog selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Visible composer container found using:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def find_linkedin_textbox(driver):
    css_candidates = [
        "div[role='dialog'] div.ql-editor[contenteditable='true']",
        "div[role='dialog'] div[role='textbox'][contenteditable='true']",
        "div[role='dialog'] div[contenteditable='true']",
        "div.artdeco-modal div.ql-editor[contenteditable='true']",
        "div.artdeco-modal div[role='textbox'][contenteditable='true']",
        "div.artdeco-modal div[contenteditable='true']",
        "div.ql-editor[contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true'][data-placeholder]",
        "div[contenteditable='true'][aria-multiline='true']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for selector in css_candidates:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking textbox selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    tag_name = (el.tag_name or "").lower()
                    contenteditable = (el.get_attribute("contenteditable") or "").strip().lower()
                    role = (el.get_attribute("role") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()
                    placeholder = (el.get_attribute("data-placeholder") or "").strip().lower()
                    aria_label = (el.get_attribute("aria-label") or "").strip().lower()

                    if tag_name == "textarea":
                        print("LinkedIn textbox found using textarea:", selector)
                        return el

                    if contenteditable == "true":
                        if (
                            "ql-editor" in cls
                            or role == "textbox"
                            or placeholder
                            or "textbox" in aria_label
                            or "editor" in aria_label
                            or "editor-content" in cls
                        ):
                            print("LinkedIn textbox found using selector:", selector)
                            return el
                except Exception:
                    continue
        except Exception:
            continue

    # JavaScript fallback
    try:
        js_element = driver.execute_script("""
            const els = Array.from(document.querySelectorAll('div, textarea'));
            return els.find(el => {
                const visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                if (!visible) return false;

                const tag = (el.tagName || '').toLowerCase();
                const contenteditable = (el.getAttribute('contenteditable') || '').toLowerCase();
                const role = (el.getAttribute('role') || '').toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();
                const placeholder = (el.getAttribute('data-placeholder') || '').toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();

                return (
                    tag === 'textarea' ||
                    (
                        contenteditable === 'true' &&
                        (
                            cls.includes('ql-editor') ||
                            role === 'textbox' ||
                            placeholder.length > 0 ||
                            aria.includes('textbox') ||
                            aria.includes('editor')
                        )
                    )
                );
            }) || null;
        """)
        if js_element:
            print("LinkedIn textbox found using JavaScript fallback")
            return js_element
    except Exception as e:
        print("Textbox JavaScript fallback failed:", str(e))

    return None


def wait_for_linkedin_composer(driver, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        dialog = find_visible_dialog(driver)

        # Step 1: ensure dialog is visible first
        if dialog:
            print("Dialog detected, waiting for editor to load...")

            # Step 2: give extra time for LinkedIn editor to mount
            time.sleep(2)

            textbox = find_linkedin_textbox(driver)

            if textbox:
                print("LinkedIn textbox detected")
                return dialog, textbox

        time.sleep(0.5)

    return None, None


def type_into_linkedin_editor(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)

        try:
            safe_click(driver, textbox)
        except Exception:
            driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        time.sleep(0.5)

        try:
            active = driver.switch_to.active_element
            if active and active.is_displayed():
                textbox = active
                print("Using active element as textbox")
        except Exception:
            pass

        # Clear content
        try:
            textbox.send_keys(Keys.CONTROL + "a")
            textbox.send_keys(Keys.DELETE)
            time.sleep(0.5)
        except Exception:
            pass

        # Main typing
        try:
            for ch in text:
                textbox.send_keys(ch)
                time.sleep(0.03)
            print("Caption typed using send_keys")
            return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # JS fallback
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if (document.activeElement !== el) {
                    el.click();
                    el.focus();
                }

                if ('value' in el) {
                    el.value = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return;
                }

                el.innerHTML = '';
                el.textContent = text;

                el.dispatchEvent(new InputEvent('beforeinput', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    data: text,
                    inputType: 'insertText'
                }));

                el.dispatchEvent(new KeyboardEvent('keyup', {
                    bubbles: true,
                    key: ' ',
                    code: 'Space'
                }));
            """, textbox, text)

            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_linkedin_editor error:", str(e))
        return False


def find_post_button(driver, dialog=None):
    search_root = dialog if dialog is not None else driver

    for selector in POST_BUTTON_SELECTORS:
        try:
            local_selector = selector.replace("div[role='dialog'] ", "")
            elements = search_root.find_elements(By.CSS_SELECTOR, local_selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        text = (btn.text or "").strip().lower()
                        aria = (btn.get_attribute("aria-label") or "").strip().lower()
                        if "post" in text or "post" in aria or True:
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
            body_preview = driver.execute_script("return document.body.innerText.slice(0, 2000);")
            print("Page text preview:", body_preview)
        except Exception:
            pass

        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception:
            pass

        close_linkedin_popups(driver)

        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                start_post_button
            )
            time.sleep(1)

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                try:
                    start_post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", start_post_button)
                    print("Start post clicked using JavaScript fallback")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        # Give LinkedIn time to open modal + load editor
        time.sleep(2)

        # Extra wait for async editor rendering
        for i in range(5):
            print(f"Waiting for editor render... {i+1}")
            time.sleep(1)

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        dialog, textbox = wait_for_linkedin_composer(driver, timeout=12)

        if not dialog or not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer opened visually but textbox was not detected. Screenshot: {screenshot}"
            }

        try:
            outer_html = driver.execute_script("return arguments[0].outerHTML;", textbox)
            print("Textbox outerHTML:", outer_html[:1000] if outer_html else "None")
        except Exception:
            pass

        typed = type_into_linkedin_editor(driver, textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        post_button = find_post_button(driver, dialog=dialog)
        if not post_button:
            post_button = find_post_button(driver)

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
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"LinkedIn post button click failed: {str(e)}. Screenshot: {screenshot}"
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