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


def find_start_post_button(driver):
    # First try strict CSS selectors only
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using CSS:", selector)
                        print("Button text:", (el.text or "").strip())
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # Strict XPath fallback only
    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and @aria-label='Start a post']",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        print("Button text:", (el.text or "").strip())
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def find_visible_dialog(driver):
    try:
        dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
        print("Dialogs found:", len(dialogs))
        for dialog in dialogs:
            try:
                if dialog.is_displayed():
                    return dialog
            except Exception:
                continue
    except Exception:
        pass
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


from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def type_into_linkedin_editor(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)

        try:
            safe_click(driver, textbox)
        except Exception:
            driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)

        # focus
        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(0.5)

        # sometimes active element becomes the real editor after click
        active = driver.switch_to.active_element
        try:
            if active and active.is_displayed():
                textbox = active
                print("Using active element as textbox")
        except Exception:
            pass

        # clear existing content
        try:
            textbox.send_keys(Keys.CONTROL, "a")
            textbox.send_keys(Keys.DELETE)
            time.sleep(0.5)
        except Exception:
            pass

        # First try normal send_keys
        try:
            for ch in text:
                textbox.send_keys(ch)
                time.sleep(0.03)
            print("Caption typed using send_keys")
            return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # JS fallback for React/LinkedIn editor
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if (document.activeElement !== el) {
                    el.click();
                    el.focus();
                }

                // Clear content
                el.innerHTML = '';
                el.textContent = text;

                el.dispatchEvent(new InputEvent('beforeinput', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    data: text,
                    inputType: 'insertText'
                }));

                el.dispatchEvent(new KeyboardEvent('keyup', {
                    bubbles: true,
                    key: ' ',
                    code: 'Space'
                }));
            """, textbox, text)

            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_linkedin_editor error:", str(e))
        return False


def find_post_button(driver, dialog=None):
    search_root = dialog if dialog is not None else driver

    for selector in POST_BUTTON_SELECTORS:
        try:
            local_selector = selector.replace("div[role='dialog'] ", "")
            elements = search_root.find_elements(By.CSS_SELECTOR, local_selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using CSS:", selector)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        ".//button[contains(@class,'share-actions__primary-action')]",
        ".//button[@aria-label='Post']",
        ".//button[contains(@aria-label,'Post')]",
        ".//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = search_root.find_elements(By.XPATH, xpath)
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

        dialog, textbox = wait_for_linkedin_composer(driver, timeout=12)

        if not dialog or not textbox:
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

        post_button = find_post_button(driver, dialog=dialog)
        if not post_button:
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
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }