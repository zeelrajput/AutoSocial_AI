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

    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button' or self::button][1]",
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
                    continue
        except Exception:
            continue

    return None

def activate_linkedin_composer(driver):
    xpath_candidates = [
        "//div[contains(@class,'ql-editor')]",
        "//div[@role='textbox']",
        "//div[contains(@class,'share-creation-state')]",
        "//div[contains(@class,'editor')]",
        "//div[contains(@class,'artdeco-modal')]//div",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    time.sleep(1)

                    el.click()
                    print("Clicked REAL editor using:", xpath)
                    time.sleep(2)
                    return True

                except Exception:
                    continue
        except Exception:
            continue

    return False

def type_into_active_element(driver, caption):
    """
    Type into whichever element currently has focus.
    This is much more reliable for LinkedIn than searching textbox selectors.
    """
    try:
        active = driver.switch_to.active_element
        print("Active element tag:", active.tag_name)

        try:
            active.send_keys(Keys.CONTROL, "a")
            active.send_keys(Keys.DELETE)
        except Exception:
            pass

        try:
            active.send_keys(caption)
            print("Caption typed using active element send_keys")
            time.sleep(1)
            return True
        except Exception as e:
            print("Active element send_keys failed:", str(e))

        try:
            ActionChains(driver).send_keys(caption).perform()
            print("Caption typed using ActionChains")
            time.sleep(1)
            return True
        except Exception as e:
            print("ActionChains typing failed:", str(e))

        try:
            driver.execute_script("""
                const el = document.activeElement;
                const text = arguments[0];

                if (!el) return false;

                el.focus();

                if ('value' in el) {
                    el.value = text;
                } else if ('textContent' in el) {
                    el.textContent = text;
                } else if ('innerHTML' in el) {
                    el.innerHTML = text;
                }

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            """, caption)
            print("Caption typed using document.activeElement JS fallback")
            time.sleep(1)
            return True
        except Exception as e:
            print("JS activeElement typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_active_element error:", str(e))
        return False

def wait_for_composer_surface(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            start_post_text = driver.find_elements(
                By.XPATH,
                "//*[contains(normalize-space(),'Start a post')]"
            )
            post_buttons = driver.find_elements(
                By.XPATH,
                "//button[@aria-label='Post' or contains(@aria-label,'Post') or .//span[normalize-space()='Post']]"
            )

            print("Start-post labels:", len(start_post_text))
            print("Possible post buttons:", len(post_buttons))

            # If a post button is visible, composer is likely open
            for btn in post_buttons:
                try:
                    if btn.is_displayed():
                        print("Composer surface detected from visible Post button")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(1)

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

        opened = wait_for_composer_surface(driver, timeout=8)
        if not opened:
            # still try activation even if detection failed
            print("Composer surface not confidently detected, continuing with activation fallback")

        activated = activate_linkedin_composer(driver)
        if not activated:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_activation_failed")
            return {
                "success": False,
                "message": f"LinkedIn composer activation failed. Screenshot: {screenshot}"
            }
        
        try:
            active = driver.switch_to.active_element
            print("Focused tag:", active.tag_name)
            print("Focused outerHTML:", driver.execute_script("return arguments[0].outerHTML;", active)[:500])
        except Exception as e:
            print("Could not inspect active element:", str(e))

        # 👉 THEN typing starts
        typed = type_into_active_element(driver, post.caption)

        typed = type_into_active_element(driver, post.caption)
        if not typed:
            # tab once and retry
            try:
                ActionChains(driver).send_keys(Keys.TAB).perform()
                time.sleep(1)
                typed = type_into_active_element(driver, post.caption)
            except Exception:
                pass

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
