import time
from selenium.webdriver.common.by import By

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
    # First: strict CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using CSS:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # Strict XPath selectors
    strict_xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and @aria-label='Start a post']",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//button[contains(@class,'share-box-feed-entry__trigger')]",
        "//div[contains(@class,'share-box-feed-entry__trigger')]",
    ]

    for xpath in strict_xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using strict XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # Text fallback
    text_xpath_candidates = [
        "//span[contains(normalize-space(),'Start a post')]",
        "//div[contains(normalize-space(),'Start a post')]",
    ]

    for xpath in text_xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    clickable = driver.execute_script("""
                        let node = arguments[0];
                        while (node) {
                            const role = node.getAttribute && node.getAttribute('role');
                            const tag = node.tagName ? node.tagName.toLowerCase() : '';
                            const aria = (node.getAttribute && node.getAttribute('aria-label') || '').toLowerCase();
                            const cls = (node.className || '').toString().toLowerCase();

                            if (
                                tag === 'button' ||
                                role === 'button' ||
                                aria.includes('start a post') ||
                                cls.includes('share-box-feed-entry__trigger')
                            ) {
                                return node;
                            }
                            node = node.parentElement;
                        }
                        return null;
                    """, el)

                    if clickable:
                        print("Start post button found using text fallback:", xpath)
                        return clickable
                except Exception:
                    continue
        except Exception:
            continue

    return None

def find_linkedin_textbox(driver):
    # First: find dialog
    dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
    for dialog in dialogs:
        try:
            if not dialog.is_displayed():
                continue

            # Search textbox only inside this dialog
            candidates = dialog.find_elements(By.CSS_SELECTOR, """
                div.ql-editor[contenteditable='true'],
                div[role='textbox'][contenteditable='true'],
                div[contenteditable='true'][role='textbox'],
                div[contenteditable='true'][data-placeholder],
                div[contenteditable='true'][aria-multiline='true'],
                div[contenteditable='true']
            """)

            for el in candidates:
                try:
                    if not el.is_displayed():
                        continue

                    contenteditable = (el.get_attribute("contenteditable") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()
                    role = (el.get_attribute("role") or "").strip().lower()
                    placeholder = (el.get_attribute("data-placeholder") or "").strip().lower()
                    aria_label = (el.get_attribute("aria-label") or "").strip().lower()

                    if contenteditable == "true":
                        if (
                            "ql-editor" in cls
                            or role == "textbox"
                            or placeholder
                            or "text editor" in aria_label
                            or "textbox" in aria_label
                        ):
                            print("LinkedIn textbox found inside dialog")
                            return el
                except Exception:
                    continue
        except Exception:
            continue

    # Fallback global search
    for selector in TEXTBOX_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed() and (el.get_attribute("contenteditable") or "").lower() == "true":
                        print("LinkedIn textbox found using fallback:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None

def wait_for_linkedin_composer(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        textbox = find_linkedin_textbox(driver)
        if textbox:
            print("LinkedIn composer detected")
            return True
        time.sleep(0.5)

    return False

def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using CSS:", selector)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    xpath_selectors = [
        "//button[contains(@class,'share-actions__primary-action')]",
        "//button[@aria-label='Post']",
        "//button[contains(@aria-label,'Post')]",
        "//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_selectors:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
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

        # IMPORTANT: this block must be outside the above if
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_post_button)
            time.sleep(1)

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Start post clicked using JavaScript")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed. Screenshot: {screenshot}"
            }

        time.sleep(3)

        opened = wait_for_linkedin_composer(driver, timeout=5)
        if not opened:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Retried Start post with JavaScript click")
            except Exception:
                pass

        time.sleep(3)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        opened = wait_for_linkedin_composer(driver, timeout=8)
        if not opened:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer did not open. Screenshot: {screenshot}"
            }

        textbox = find_linkedin_textbox(driver)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

            typed = type_into_linkedin_editor(driver, textbox, post.caption)

        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];
                    el.focus();

                    if (el.innerHTML !== undefined) {
                        el.innerHTML = text;
                        el.dispatchEvent(new InputEvent('input', { bubbles: true }));
                    } else {
                        el.value = text;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                """, textbox, post.caption)
                print("Caption typed using JavaScript fallback")
                typed = True
            except Exception as e:
                screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
                return {
                    "success": False,
                    "message": f"Typing failed: {str(e)}. Screenshot: {screenshot}"
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
