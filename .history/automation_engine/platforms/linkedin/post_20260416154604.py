import time
from selenium.webdriver.common.by import By

from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def find_start_post_button(driver):
    # First: direct CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    text = (element.text or "").strip().lower()
                    aria = (element.get_attribute("aria-label") or "").strip().lower()

                    if (
                        "start a post" in text
                        or "start a post" in aria
                        or "share-box-feed-entry" in (element.get_attribute("class") or "")
                    ):
                        print("Start post button found using CSS:", selector)
                        return element
                except Exception:
                    continue
        except Exception:
            continue

    # Second: text-based XPath
    xpath_selectors = [
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
        "//button[contains(., 'Start a post')]",
        "//div[@role='button' and contains(., 'Start a post')]",
        "//*[contains(@aria-label, 'Start a post')]",
    ]

    for xpath in xpath_selectors:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for element in elements:
                try:
                    if element.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        return element
                except Exception:
                    continue
        except Exception:
            continue

    # Third: JavaScript fallback
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
                    cls.includes('share-box-feed-entry--closed')
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
        print("JS fallback failed:", str(e))

    return None

def get_visible_dialog(driver):
    dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
    print("DEBUG: total dialogs found =", len(dialogs))

    for i, dialog in enumerate(dialogs):
        try:
            visible = driver.execute_script("""
                const el = arguments[0];
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            """, dialog)

            if visible:
                print(f"DEBUG: visible dialog found at index {i}")
                return dialog
        except Exception:
            continue

    return None


def find_textbox_in_dialog(dialog):
    selectors = [
        "div.ql-editor[contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for selector in selectors:
        try:
            elements = dialog.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_enabled():
                        print("Textbox found in dialog using:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue
    return None


def find_post_button_in_dialog(dialog):
    for selector in POST_BUTTON_SELECTORS:
        try:
            elements = dialog.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                try:
                    if btn.is_enabled():
                        print("Post button found in dialog using:", selector)
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
        return {"success": False, "message": f"Start post button not found. Screenshot: {screenshot}"}

    try:
        clicked = safe_click(driver, start_post_button)
        if not clicked:
            driver.execute_script("arguments[0].click();", start_post_button)
        print("LinkedIn 'Start a post' button clicked")
    except Exception:
        screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
        return {"success": False, "message": f"Start post click failed. Screenshot: {screenshot}"}

        print("LinkedIn 'Start a post' button clicked")
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        time.sleep(5)

        dialog = get_visible_dialog(driver)
        if not dialog:
            screenshot = save_screenshot(driver, prefix="linkedin_dialog_not_found")
            return {"success": False, "message": f"Visible LinkedIn dialog not found. Screenshot: {screenshot}"}

        print("DEBUG dialog snippet:", dialog.get_attribute("outerHTML")[:2000])

        textbox = find_textbox_in_dialog(dialog)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"}

        safe_click(driver, textbox)

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        try:
            type_like_human(textbox, post.caption)
        except Exception:
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

        time.sleep(2)

        post_button = find_post_button_in_dialog(dialog)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {"success": False, "message": f"LinkedIn post button not found. Screenshot: {screenshot}"}

        clicked = safe_click(driver, post_button)
        if not clicked:
            driver.execute_script("arguments[0].click();", post_button)

        medium_pause()
        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}