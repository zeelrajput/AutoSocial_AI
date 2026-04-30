import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
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


def react_click(driver, element):
    driver.execute_script("""
        const el = arguments[0];
        const rect = el.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        ['mouseover', 'mousedown', 'mouseup', 'click'].forEach(type => {
            el.dispatchEvent(new MouseEvent(type, {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: x,
                clientY: y,
                button: 0
            }));
        });
    """, element)
    print("Dispatched React-compatible click events")


def find_start_post_button(driver):
    # CSS selectors
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

    # XPath fallback
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

    # JavaScript fallback
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


def save_dom_snapshot(driver, filename_prefix="linkedin_dom_snapshot"):
    try:
        html = driver.page_source
        timestamp = int(time.time())
        path = f"screenshots/{filename_prefix}_{timestamp}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"DOM snapshot saved: {path}")
        return path
    except Exception as e:
        print("Failed to save DOM snapshot:", str(e))
        return None


def activate_linkedin_composer(driver):
    xpath_candidates = [
        "//*[contains(text(),'What do you want to talk about?')]",
        "//*[contains(text(),\"What's one cold email you still remember?\")]",
        "//*[contains(text(),'What’s one cold email you still remember?')]",
        "//*[contains(text(),'Talk about')]",
        "//*[contains(text(),'Share')]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"Checking composer activation xpath: {xpath} -> found {len(elements)}")
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    time.sleep(0.5)

                    try:
                        el.click()
                    except Exception:
                        react_click(driver, el)

                    print("Composer placeholder clicked")
                    time.sleep(1)
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def find_linkedin_editor(driver):
    selectors = [
        "div[contenteditable='true']",
        "div[role='textbox']",
        "div.ql-editor",
        "textarea",
        "[data-placeholder]",
        "[aria-placeholder]",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking editor selector: {selector} -> found {len(elements)}")
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    tag = (el.tag_name or "").lower()
                    cls = (el.get_attribute("class") or "").lower()
                    role = (el.get_attribute("role") or "").lower()
                    ce = (el.get_attribute("contenteditable") or "").lower()
                    dp = (el.get_attribute("data-placeholder") or "").lower()
                    ap = (el.get_attribute("aria-placeholder") or "").lower()
                    aria = (el.get_attribute("aria-label") or "").lower()

                    if (
                        tag == "textarea"
                        or ce == "true"
                        or role == "textbox"
                        or "ql-editor" in cls
                        or dp
                        or ap
                        or "editor" in aria
                        or "textbox" in aria
                    ):
                        print("LinkedIn editor found")
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    try:
        active = driver.switch_to.active_element
        if active and active.is_displayed():
            print("Using active element as editor fallback")
            return active
    except Exception:
        pass

    return None


def wait_for_linkedin_composer(driver, timeout=20):
    end_time = time.time() + timeout
    print("Waiting for LinkedIn composer to appear...")

    while time.time() < end_time:
        remaining = int(end_time - time.time())
        print(f"Composer wait attempt #{timeout - remaining} ({remaining}s left)")

        # Try activation first
        activate_linkedin_composer(driver)

        editor = find_linkedin_editor(driver)
        if editor:
            print("✅ LinkedIn composer/editor detected")
            return editor

        time.sleep(1)

    print("❌ Composer not found after timeout")
    return None


def type_into_linkedin_composer(driver, text):
    try:
        # Step 1: activate visible composer/placeholder
        activate_linkedin_composer(driver)
        time.sleep(1)

        # Step 2: get editor
        editor = find_linkedin_editor(driver)
        if not editor:
            print("No editor found")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", editor)
        time.sleep(0.5)

        # Step 3: click editor
        try:
            editor.click()
        except Exception:
            react_click(driver, editor)

        time.sleep(0.5)

        # Step 4: use active element after click
        try:
            active = driver.switch_to.active_element
            if active and active.is_displayed():
                editor = active
                print("Typing into active element")
                try:
                    print("Active tag:", active.tag_name)
                    print("Active class:", active.get_attribute("class"))
                    print("Active role:", active.get_attribute("role"))
                    print("Active contenteditable:", active.get_attribute("contenteditable"))
                except Exception:
                    pass
        except Exception:
            pass

        # Step 5: focus
        try:
            driver.execute_script("arguments[0].focus();", editor)
        except Exception:
            pass

        time.sleep(0.3)

        # Step 6: clear old text if any
        try:
            editor.send_keys(Keys.CONTROL + "a")
            editor.send_keys(Keys.DELETE)
            time.sleep(0.3)
        except Exception:
            pass

        # Step 7: normal send_keys
        try:
            for ch in text:
                editor.send_keys(ch)
                time.sleep(0.03)
            print("Caption typed using send_keys")
            return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # Step 8: ActionChains fallback
        try:
            ActionChains(driver).move_to_element(editor).click().pause(0.3).send_keys(text).perform()
            print("Caption typed using ActionChains")
            return True
        except Exception as e:
            print("ActionChains failed:", str(e))

        # Step 9: JavaScript fallback
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.click();
                el.focus();

                const target = document.activeElement || el;

                if ('value' in target) {
                    target.value = text;
                    target.dispatchEvent(new Event('input', { bubbles: true }));
                    target.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }

                target.textContent = text;
                target.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    data: text,
                    inputType: 'insertText'
                }));
                return true;
            """, editor, text)

            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_linkedin_composer error:", str(e))
        return False


def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking post button selector: {selector} -> found {len(elements)}")
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        text = (btn.text or "").strip().lower()
                        aria = (btn.get_attribute("aria-label") or "").strip().lower()

                        if "post" in text or "post" in aria or "publish" in text:
                            print("Post button found using CSS:", selector)
                            return btn
                except Exception:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action')]",
        "//button[@aria-label='Post']",
        "//button[contains(@aria-label,'Post')]",
        "//span[normalize-space()='Post']/ancestor::button[1]",
        "//button[contains(., 'Post')]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"Checking post button xpath: {xpath} -> found {len(elements)}")
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
            body_preview = driver.execute_script("return document.body.innerText.slice(0, 3000);")
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
                    react_click(driver, start_post_button)
                    print("Start post clicked using JavaScript fallback")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        save_dom_snapshot(driver, filename_prefix="after_start_post_click")

        time.sleep(2)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        editor = wait_for_linkedin_composer(driver, timeout=20)
        if not editor:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer opened visually but textbox was not detected. Screenshot: {screenshot}"
            }

        typed = type_into_linkedin_composer(driver, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

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
                    react_click(driver, post_button)
                    print("Post button clicked using JavaScript fallback")

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
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }