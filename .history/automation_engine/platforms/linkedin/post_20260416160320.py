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
    # 1) Strict CSS selectors first
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    if not element.is_displayed():
                        continue

                    text = (element.text or "").strip().lower()
                    aria = (element.get_attribute("aria-label") or "").strip().lower()
                    cls = (element.get_attribute("class") or "").strip().lower()

                    if (
                        "start a post" in text
                        or "start a post" in aria
                        or "share-box-feed-entry" in cls
                    ):
                        print("Start post button found using CSS:", selector)
                        return element
                except Exception:
                    continue
        except Exception:
            continue

    # 2) XPath fallbacks
    xpath_candidates = [
        "//button[contains(normalize-space(),'Start a post')]",
        "//div[@role='button' and contains(normalize-space(),'Start a post')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
        "//*[@aria-label='Start a post']",
        "//*[contains(@aria-label,'Start a post')]",
    ]

    for xpath in xpath_candidates:
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
                            if (tag === 'button' || role === 'button') {
                                return node;
                            }
                            node = node.parentElement;
                        }
                        return arguments[0];
                    """, el)

                    if clickable:
                        print("Start post button found using XPath:", xpath)
                        return clickable
                except Exception:
                    continue
        except Exception:
            continue

    # 3) JS fallback
    try:
        element = driver.execute_script("""
            const nodes = Array.from(document.querySelectorAll('button, div[role="button"], span, div'));
            for (const el of nodes) {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();

                if (
                    text.includes('start a post') ||
                    aria.includes('start a post') ||
                    cls.includes('share-box-feed-entry__trigger') ||
                    cls.includes('share-box-feed-entry')
                ) {
                    return el;
                }
            }
            return null;
        """)
        if element:
            print("Start post button found using JavaScript fallback")
            return element
    except Exception as e:
        print("Start post JS fallback failed:", str(e))

    return None


def find_linkedin_textbox(driver):
    # Global search - do NOT depend on dialog
    for selector in TEXTBOX_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    contenteditable = (el.get_attribute("contenteditable") or "").strip().lower()
                    text = (el.text or "").strip().lower()
                    aria = (el.get_attribute("aria-label") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()

                    if contenteditable == "true":
                        print("Textbox found using CSS:", selector)
                        return el

                    if "what do you want to talk about" in text:
                        print("Textbox found using visible text:", selector)
                        return el

                    if "textbox" in aria or "editor" in aria or "ql-editor" in cls:
                        print("Textbox found using aria/class:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    xpath_selectors = [
        "//div[@contenteditable='true']",
        "//div[contains(@class,'ql-editor') and @contenteditable='true']",
        "//div[@role='textbox' and @contenteditable='true']",
        "//textarea",
    ]

    for xpath in xpath_selectors:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Textbox found using XPath:", xpath)
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

        try:
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

        time.sleep(2)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        opened = wait_for_linkedin_composer(driver, timeout=10)
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

        try:
            safe_click(driver, textbox)
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        try:
            type_like_human(textbox, post.caption)
            print("Caption typed using type_like_human")
        except Exception:
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