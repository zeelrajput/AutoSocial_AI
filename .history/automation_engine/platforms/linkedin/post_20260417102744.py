import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.common.type_helper import type_like_human
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def find_start_post_button(driver):
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using CSS:", selector)
                        return el
                except Exception:
                    pass
        except Exception:
            pass

    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button' or self::button][1]",
        "//div[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button' or self::button][1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        return el
                except Exception:
                    pass
        except Exception:
            pass

    return None


def find_linkedin_textbox(driver):
    selectors = [
        # most specific
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true'][role='textbox']",
        "div.ql-editor[contenteditable='true']",
        "div[contenteditable='true'][aria-multiline='true']",
        "div[contenteditable='true'][data-placeholder]",
        "div[contenteditable='true'][aria-label*='text editor' i]",
        "div[contenteditable='true'][aria-label*='create a post' i]",
        "div[contenteditable='true']",
    ]

    # first try visible dialog/modal area
    modal_roots = driver.find_elements(
        By.CSS_SELECTOR,
        "div[role='dialog'], div.artdeco-modal, div.share-box-feed-entry__closed, div.share-creation-state"
    )

    for root in modal_roots:
        try:
            if not root.is_displayed():
                continue
            for selector in selectors:
                try:
                    elements = root.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        try:
                            if el.is_displayed():
                                print("LinkedIn textbox found inside modal using:", selector)
                                return el
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    # fallback global search
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("LinkedIn textbox found globally using:", selector)
                        return el
                except Exception:
                    pass
        except Exception:
            pass

    return None


def wait_for_linkedin_composer(driver, timeout=15):
    end_time = time.time() + timeout
    while time.time() < end_time:
        textbox = find_linkedin_textbox(driver)
        if textbox:
            print("LinkedIn composer detected")
            return textbox
        time.sleep(0.5)
    return None


def type_into_linkedin_editor(driver, textbox, caption):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)

        try:
            safe_click(driver, textbox)
        except Exception:
            pass

        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(0.5)

        # clear existing content
        try:
            textbox.send_keys(Keys.CONTROL, "a")
            textbox.send_keys(Keys.DELETE)
        except Exception:
            pass

        # normal typing
        try:
            type_like_human(textbox, caption)
            time.sleep(1)

            current_text = (textbox.text or "").strip()
            if caption.strip() in current_text or current_text:
                print("Caption typed with keyboard")
                return True
        except Exception as e:
            print("Keyboard typing failed:", str(e))

        # JS fallback
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];
                el.focus();

                if (el.innerHTML !== undefined) {
                    el.innerHTML = '';
                    el.innerText = text;
                    el.textContent = text;
                }

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    data: text,
                    inputType: 'insertText'
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
            """, textbox, caption)

            time.sleep(1)
            print("Caption typed using JavaScript fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))
            return False

    except Exception as e:
        print("type_into_linkedin_editor error:", str(e))
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
                    pass
        except Exception:
            pass

    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action')]",
        "//button[@aria-label='Post']",
        "//button[contains(@aria-label,'Post')]",
        "//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using XPath:", xpath)
                        return btn
                except Exception:
                    pass
        except Exception:
            pass

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

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed. Screenshot: {screenshot}"
            }

        time.sleep(3)

        textbox = wait_for_linkedin_composer(driver, timeout=15)
        if not textbox:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                time.sleep(3)
                textbox = wait_for_linkedin_composer(driver, timeout=8)
            except Exception:
                pass

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer opened visually but textbox was not detected. Screenshot: {screenshot}"
            }

        typed = type_into_linkedin_editor(driver, textbox, post.caption)
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