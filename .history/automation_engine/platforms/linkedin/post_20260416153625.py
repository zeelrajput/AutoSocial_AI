import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
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


def get_visible_dialog(driver):
    dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
    print("DEBUG: total dialogs found =", len(dialogs))

    # First try normal Selenium displayed check
    for i, dialog in enumerate(dialogs):
        try:
            if dialog.is_displayed():
                print(f"DEBUG: visible dialog found by Selenium at index {i}")
                return dialog
        except Exception:
            continue

    # Fallback: JS visibility check
    for i, dialog in enumerate(dialogs):
        try:
            visible = driver.execute_script("""
                const el = arguments[0];
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    style.opacity !== '0' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            """, dialog)

            if visible:
                print(f"DEBUG: visible dialog found by JS at index {i}")
                return dialog
        except Exception:
            continue

    # Last fallback: return the largest dialog
    largest_dialog = None
    largest_area = 0

    for i, dialog in enumerate(dialogs):
        try:
            area = driver.execute_script("""
                const r = arguments[0].getBoundingClientRect();
                return r.width * r.height;
            """, dialog)

            if area > largest_area:
                largest_area = area
                largest_dialog = dialog
        except Exception:
            continue

    if largest_dialog:
        print(f"DEBUG: using largest dialog fallback with area {largest_area}")
        return largest_dialog

    return None


def find_textbox_in_dialog(dialog):
    css_selectors = [
        "div.ql-editor[contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for selector in css_selectors:
        try:
            elements = dialog.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Textbox found in dialog using CSS:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    xpath_selectors = [
        ".//div[contains(@class,'ql-editor') and @contenteditable='true']",
        ".//div[@role='textbox' and @contenteditable='true']",
        ".//div[@contenteditable='true']",
        ".//textarea",
    ]

    for xpath in xpath_selectors:
        try:
            elements = dialog.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Textbox found in dialog using XPath:", xpath)
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
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found in dialog using CSS:", selector)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    xpath_selectors = [
        ".//button[contains(@aria-label,'Post')]",
        ".//button[contains(@class,'share-actions__primary-action')]",
        ".//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_selectors:
        try:
            elements = dialog.find_elements(By.XPATH, xpath)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found in dialog using XPath:", xpath)
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

        clicked = safe_click(driver, start_post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
                return {
                    "success": False,
                    "message": f"Start post click failed. Screenshot: {screenshot}"
                }

        print("LinkedIn 'Start a post' button clicked")
        time.sleep(5)

        dialog = get_visible_dialog(driver)
        if not dialog:
            screenshot = save_screenshot(driver, prefix="linkedin_dialog_not_found")
            return {
                "success": False,
                "message": f"Visible LinkedIn dialog not found. Screenshot: {screenshot}"
            }

        textbox = find_textbox_in_dialog(dialog)
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

        print("Textbox clicked/focused")

        typed = False
        try:
            type_like_human(textbox, post.caption)
            typed = True
            print("Caption typed using type_like_human")
        except Exception:
            pass

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
                typed = True
                print("Caption typed using JavaScript fallback")
            except Exception as e:
                screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
                return {
                    "success": False,
                    "message": f"Typing failed: {str(e)}. Screenshot: {screenshot}"
                }

        time.sleep(2)
        medium_pause()

        post_button = find_post_button_in_dialog(dialog)
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