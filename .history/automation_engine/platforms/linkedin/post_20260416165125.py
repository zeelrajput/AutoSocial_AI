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
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
    ]

    for xpath in strict_xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def find_composer_surface(driver):
    xpath_candidates = [
        "//*[contains(normalize-space(), 'What do you want to talk about?')]",
        "//div[contains(@class,'share-box')]//*[contains(normalize-space(), 'What do you want to talk about?')]",
        "//div[contains(@class,'ql-editor')]",
        "//div[@contenteditable='true']",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Composer surface found using XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def wait_for_composer_surface(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        surface = find_composer_surface(driver)
        if surface:
            print("LinkedIn composer surface detected")
            return surface
        time.sleep(0.5)

    return None


def find_real_textbox(driver):
    css_candidates = [
        "div.ql-editor[contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for selector in css_candidates:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Real textbox found using CSS:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        "//div[contains(@class,'ql-editor') and @contenteditable='true']",
        "//div[@role='textbox' and @contenteditable='true']",
        "//div[@contenteditable='true']",
        "//textarea",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Real textbox found using XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def activate_editor_and_get_textbox(driver, timeout=8):
    end_time = time.time() + timeout

    while time.time() < end_time:
        surface = find_composer_surface(driver)
        if surface:
            try:
                safe_click(driver, surface)
                print("Clicked composer surface")
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", surface)
                    print("Clicked composer surface using JavaScript")
                except Exception:
                    pass

            time.sleep(1)

        textbox = find_real_textbox(driver)
        if textbox:
            try:
                safe_click(driver, textbox)
            except Exception:
                pass

            try:
                driver.execute_script("arguments[0].focus();", textbox)
            except Exception:
                pass

            time.sleep(0.5)
            return textbox

        time.sleep(0.5)

    return None


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

        time.sleep(2)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        surface = wait_for_composer_surface(driver, timeout=8)
        if not surface:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Retried Start post with JavaScript click")
            except Exception:
                pass

            surface = wait_for_composer_surface(driver, timeout=6)

        if not surface:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer did not open. Screenshot: {screenshot}"
            }

        textbox = activate_editor_and_get_textbox(driver, timeout=10)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found/activated. Screenshot: {screenshot}"
            }

        typed = False

        try:
            type_like_human(textbox, post.caption)
            print("Caption typed using type_like_human")
            typed = True
        except Exception:
            pass

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];
                    el.focus();

                    if (el.innerHTML !== undefined) {
                        el.innerHTML = '';
                        el.innerHTML = text;
                        el.dispatchEvent(new InputEvent('input', {
                            bubbles: true,
                            data: text,
                            inputType: 'insertText'
                        }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    } else {
                        el.value = text;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
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