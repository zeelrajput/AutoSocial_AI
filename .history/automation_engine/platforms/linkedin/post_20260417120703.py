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
                        print("Button text:", (el.text or "").strip())
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

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

def find_linkedin_textbox(dialog):
    selectors = [
        "div.ql-editor[contenteditable='true']",
        "div[role='textbox'][contenteditable='true']",
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true'][data-placeholder]",
        "div[contenteditable='true'][aria-placeholder]",
    ]

    for selector in selectors:
        try:
            elements = dialog.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Textbox found using selector:", selector)
                        print("OuterHTML:", driver.execute_script("return arguments[0].outerHTML;", el)[:500])
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        ".//div[contains(@class,'ql-editor') and @contenteditable='true']",
        ".//div[@role='textbox' and @contenteditable='true']",
        ".//div[@contenteditable='true']",
    ]

    for xpath in xpath_candidates:
        try:
            elements = dialog.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Textbox found using XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def wait_for_linkedin_composer(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        dialog = find_visible_dialog(driver)
        if dialog:
            print("Visible dialog found")
            textbox = find_linkedin_textbox(dialog)
            if textbox:
                print("LinkedIn composer detected")
                return dialog, textbox

        try:
            dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
            print("Dialogs found:", len(dialogs))
        except Exception:
            pass

        time.sleep(1)

    return None, None

def type_into_linkedin_editor(driver, textbox, caption):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        time.sleep(1)

        try:
            safe_click(driver, textbox)
        except Exception:
            try:
                textbox.click()
            except Exception:
                driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)
        driver.execute_script("arguments[0].focus();", textbox)

        # Try send_keys first
        try:
            textbox.send_keys(caption)
            time.sleep(1)

            current_text = (textbox.text or "").strip()
            if caption.strip() in current_text or current_text:
                print("Caption typed using send_keys")
                return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # Try active element typing
        try:
            active = driver.switch_to.active_element
            active.send_keys(caption)
            time.sleep(1)
            print("Caption typed using active element")
            return True
        except Exception as e:
            print("active element typing failed:", str(e))

        # JS fallback
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if ('innerHTML' in el) el.innerHTML = '';
                if ('textContent' in el) el.textContent = text;
                if ('value' in el) el.value = text;

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
            """, textbox, caption)

            time.sleep(1)
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
            dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
            print("Dialogs found:", len(dialogs))
        except Exception:
            dialogs = []

        try:
            print("Editable elements found:", len(driver.find_elements(By.XPATH, "//*[@contenteditable='true']")))
        except Exception:
            pass

        try:
            print("Placeholder elements found:", len(driver.find_elements(By.XPATH, "//*[@data-placeholder or @aria-placeholder]")))
        except Exception:
            pass

        # Warm-up click inside visible dialog body
        for dialog in dialogs:
            try:
                if dialog.is_displayed():
                    driver.execute_script("arguments[0].click();", dialog)
                    print("Clicked visible dialog to activate composer")
                    time.sleep(2)
                    break
            except Exception:
                pass

        # textbox = wait_for_linkedin_composer(driver, timeout=10)
        dialog, textbox = wait_for_linkedin_composer(driver, timeout=12)
        
        # Retry by clicking inside modal center
        if not textbox:
            try:
                visible_dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
                for dialog in visible_dialogs:
                    try:
                        if dialog.is_displayed():
                            driver.execute_script("""
                                const rect = arguments[0].getBoundingClientRect();
                                const x = rect.left + rect.width / 2;
                                const y = rect.top + rect.height / 2;
                                const el = document.elementFromPoint(x, y);
                                if (el) el.click();
                            """, dialog)
                            print("Clicked dialog center to activate textbox")
                            time.sleep(2)
                            break
                    except Exception:
                        pass
            except Exception:
                pass

            textbox = wait_for_linkedin_composer(driver, timeout=8)

        # Try iframe detection
        if not textbox:
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print("Iframes found:", len(iframes))

                for i, frame in enumerate(iframes):
                    try:
                        driver.switch_to.default_content()
                        driver.switch_to.frame(frame)
                        print(f"Switched to iframe index: {i}")

                        try:
                            print("Iframe editable elements:", len(driver.find_elements(By.XPATH, "//*[@contenteditable='true']")))
                        except Exception:
                            pass

                        textbox = find_linkedin_textbox(driver)
                        if textbox:
                            print(f"Textbox found inside iframe index: {i}")
                            break
                    except Exception:
                        continue

                if not textbox:
                    driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()

        # Retry original click once more
        if not textbox:
            try:
                driver.switch_to.default_content()
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Retried Start post with JavaScript click")
                time.sleep(3)
                textbox = wait_for_linkedin_composer(driver, timeout=8)
            except Exception:
                pass

        if not textbox:
            driver.switch_to.default_content()
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
            driver.switch_to.default_content()
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        # Important: return to main content before finding post button
        driver.switch_to.default_content()

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
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }