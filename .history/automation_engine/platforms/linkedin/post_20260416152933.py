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
    for selector in START_POST_SELECTORS:
        try:
            element = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5)
            print("Start post button found using CSS:", selector)
            return element
        except Exception:
            continue
    return None


def find_textbox(driver):
    # CSS attempts
    for selector in TEXTBOX_SELECTORS:
        try:
            textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=4)
            print("Textbox found using CSS:", selector)
            return textbox
        except Exception:
            continue

    # XPath fallback attempts
    xpath_selectors = [
        "//div[contains(@class,'ql-editor') and @contenteditable='true']",
        "//div[@role='textbox' and @contenteditable='true']",
        "//div[@contenteditable='true']",
        "//textarea",
    ]

    for xpath in xpath_selectors:
        try:
            textbox = wait_for_visible(driver, By.XPATH, xpath, timeout=4)
            print("Textbox found using XPath:", xpath)
            return textbox
        except Exception:
            continue

    # JavaScript DOM fallback
    try:
        textbox = driver.execute_script("""
            const nodes = Array.from(document.querySelectorAll('[contenteditable="true"], textarea, div[role="textbox"]'));
            for (const el of nodes) {
                const visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                if (!visible) continue;
                return el;
            }
            return null;
        """)
        if textbox:
            print("Textbox found using JavaScript DOM search")
            return textbox
    except Exception as e:
        print("Textbox JS fallback failed:", str(e))

    return None


def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            button = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5)
            print("Post button found using CSS:", selector)
            return button
        except Exception:
            continue

    xpath_selectors = [
        "//button[contains(@aria-label,'Post')]",
        "//button[contains(@class,'share-actions__primary-action')]",
        "//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_selectors:
        try:
            button = wait_for_clickable(driver, By.XPATH, xpath, timeout=5)
            print("Post button found using XPath:", xpath)
            return button
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
            return {"success": False, "message": f"Start post button not found. Screenshot: {screenshot}"}

        clicked = safe_click(driver, start_post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
                return {"success": False, "message": f"Start post click failed. Screenshot: {screenshot}"}

        print("LinkedIn 'Start a post' button clicked")

        # Important: wait for composer animation/load
        time.sleep(5)

        # debug info
        try:
            dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
            print("Dialogs found on page:", len(dialogs))
        except Exception:
            pass

        textbox = find_textbox(driver)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"}

        try:
            safe_click(driver, textbox)
        except Exception:
            pass

        # extra focus fallback
        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        print("Textbox clicked/focused")

        try:
            type_like_human(textbox, post.caption)
        except Exception:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];
                    el.focus();
                    if (el.innerHTML !== undefined) {
                        el.innerHTML = text;
                        el.dispatchEvent(new InputEvent('input', {bubbles: true}));
                    } else {
                        el.value = text;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                    }
                """, textbox, post.caption)
            except Exception as e:
                screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
                return {"success": False, "message": f"Typing failed: {str(e)}. Screenshot: {screenshot}"}

        print("Caption typed")
        medium_pause()
        time.sleep(2)

        post_button = find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {"success": False, "message": f"LinkedIn post button not found. Screenshot: {screenshot}"}

        clicked = safe_click(driver, post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", post_button)
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
                return {"success": False, "message": f"LinkedIn post button click failed. Screenshot: {screenshot}"}

        print("Post published on LinkedIn")
        medium_pause()

        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}