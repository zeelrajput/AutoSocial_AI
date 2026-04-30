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
    xpath_candidates = [
        "//div[@role='dialog']//*[@contenteditable='true']",
        "//div[@role='dialog']//div[@role='textbox']",
        "//div[@role='dialog']//div[contains(@class,'ql-editor')]",
        "//div[@role='dialog']//*[@data-placeholder]",
        "//div[@role='dialog']//*[@aria-placeholder]",
        "//div[contains(@class,'artdeco-modal')]//*[@contenteditable='true']",
        "//div[contains(@class,'artdeco-modal')]//*[@data-placeholder]",
        "//*[@contenteditable='true']",
        "//*[@role='textbox']",
        "//*[@data-placeholder]",
        "//*[@aria-placeholder]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    tag_name = (el.tag_name or "").lower()
                    text = (el.text or "").strip()
                    placeholder = (
                        el.get_attribute("data-placeholder")
                        or el.get_attribute("aria-placeholder")
                        or el.get_attribute("placeholder")
                        or ""
                    ).strip()

                    outer = driver.execute_script("return arguments[0].outerHTML;", el)

                    print("Candidate textbox found using XPath:", xpath)
                    print("Tag:", tag_name)
                    print("Placeholder:", placeholder)
                    print("Visible text:", text[:200] if text else "")
                    print("OuterHTML:", outer[:500] if outer else "None")

                    return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def wait_for_linkedin_composer(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        textbox = find_linkedin_textbox(driver)
        if textbox:
            print("LinkedIn composer detected")
            return textbox

        try:
            dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
            print("Dialogs found:", len(dialogs))
        except Exception:
            pass

        try:
            editable = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")
            print("Editable elements found:", len(editable))
        except Exception:
            pass

        time.sleep(1)

    return None

def type_into_linkedin_editor(driver, textbox, caption):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        time.sleep(1)

        try:
            textbox.click()
        except Exception:
            driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)
        driver.execute_script("arguments[0].focus();", textbox)

        # Try normal send_keys first
        try:
            textbox.clear()
        except Exception:
            pass

        try:
            textbox.send_keys(caption)
            time.sleep(1)
            if caption.strip() in (textbox.text or "") or (textbox.text or "").strip() != "":
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
                el.innerHTML = '';
                el.textContent = text;
                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    inputType: 'insertText',
                    data: text
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, textbox, caption)
            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))
            return False

    except Exception as e:
        print("Typing function error:", str(e))
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
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                start_post_button
            )
            time.sleep(1)

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Start post clicked using JavaScript fallback")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        time.sleep(3)

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        try:
            print("Dialogs found:", len(driver.find_elements(By.XPATH, "//div[@role='dialog']")))
        except Exception:
            pass

        try:
            print("Editable elements found:", len(driver.find_elements(By.XPATH, "//*[@contenteditable='true']")))
        except Exception:
            pass

        textbox = wait_for_linkedin_composer(driver, timeout=15)

        if not textbox:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Retried Start post with JavaScript click")
                time.sleep(3)
                textbox = wait_for_linkedin_composer(driver, timeout=8)
            except Exception:
                pass

        if not textbox:
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
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }