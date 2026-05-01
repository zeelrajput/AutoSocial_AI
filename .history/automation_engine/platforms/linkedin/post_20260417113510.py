import time
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def find_start_post_button(driver):
    xpath_candidates = [
        # 🔥 MAIN WORKING SELECTOR (LinkedIn actual trigger)
        "//div[contains(@class,'share-box-feed-entry__trigger')]",

        # backup
        "//button[contains(@class,'share-box-feed-entry__trigger')]",

        # aria based
        "//button[@aria-label='Start a post']",
        "//div[@role='button' and @aria-label='Start a post']",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("✅ REAL Start post button found:", xpath)
                        return el
                except:
                    continue
        except:
            continue

    return None

def wait_for_modal(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
            for dialog in dialogs:
                try:
                    if dialog.is_displayed():
                        print("LinkedIn composer modal detected")
                        return dialog
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(1)

    return None


def find_textbox_in_modal(modal):
    xpath_candidates = [
        ".//div[@contenteditable='true']",
        ".//div[@role='textbox']",
        ".//div[contains(@class,'ql-editor')]",
        ".//textarea",
    ]

    for xpath in xpath_candidates:
        try:
            elements = modal.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print("Textbox found in modal using:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def type_inside_modal(driver, modal, caption):
    try:
        textbox = find_textbox_in_modal(modal)
        if not textbox:
            print("Textbox not found inside modal")
            return False

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
            time.sleep(1)
        except Exception:
            pass

        try:
            safe_click(driver, textbox)
        except Exception:
            try:
                textbox.click()
            except Exception:
                driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        try:
            textbox.send_keys(caption)
            print("Caption typed successfully")
            time.sleep(1)
            return True
        except Exception as e:
            print("Typing failed with send_keys:", str(e))

        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];
                el.focus();

                if ('innerHTML' in el) el.innerHTML = text;
                if ('textContent' in el) el.textContent = text;
                if ('value' in el) el.value = text;

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, textbox, caption)
            print("Caption typed using JS fallback")
            time.sleep(1)
            return True
        except Exception as e:
            print("Typing failed with JS fallback:", str(e))

        return False

    except Exception as e:
        print("type_inside_modal error:", str(e))
        return False


def find_post_button(driver):
    xpath_candidates = [
        "//div[@role='dialog']//button[.//span[normalize-space()='Post']]",
        "//div[@role='dialog']//button[contains(@aria-label,'Post')]",
        "//button[.//span[normalize-space()='Post']]",
        "//button[contains(@aria-label,'Post')]",
        "//button[contains(@class,'share-actions__primary-action')]",
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
                    continue
        except Exception:
            continue

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
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                start_post_button
            )
            time.sleep(1)

            try:
                start_post_button.click()
                print("Clicked start post using normal click")
            except Exception:
                clicked = safe_click(driver, start_post_button)
                if not clicked:
                    driver.execute_script("arguments[0].click();", start_post_button)
                    print("Clicked start post using JavaScript fallback")
                else:
                    print("Clicked start post using safe_click")

            time.sleep(3)

        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        modal = wait_for_modal(driver, timeout=10)
        if not modal:
            screenshot = save_screenshot(driver, prefix="linkedin_modal_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn modal not opened. Screenshot: {screenshot}"
            }

        typed = type_inside_modal(driver, modal, post.caption)
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
                    driver.execute_script("arguments[0].click();", post_button)
                    print("Post button clicked using JavaScript")
            else:
                print("Post button clicked using safe_click")

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