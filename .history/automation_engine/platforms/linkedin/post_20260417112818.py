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
    xpath_candidates = [
        # BEST selector (main container)
        "//div[contains(@class,'share-box-feed-entry__trigger')]",
        
        # fallback
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        
        # IMPORTANT: parent of text
        "//span[contains(text(),'Start a post')]/ancestor::div[@role='button'][1]",
        "//div[contains(text(),'Start a post')]/ancestor::div[@role='button'][1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found:", xpath)
                        return el
                except:
                    continue
        except:
            continue

    return None


def wait_for_prompt_text(driver, timeout=10):
    end_time = time.time() + timeout
    xpath_candidates = [
        "//*[contains(text(),'What do you want to talk about')]",
        "//*[contains(text(),'Talk about')]",
        "//*[contains(text(),'Start a post')]",
    ]

    while time.time() < end_time:
        for xpath in xpath_candidates:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed():
                            print("Prompt text found using XPath:", xpath)
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        time.sleep(1)

    return None


def activate_editor_v2(driver):
    xpath_candidates = [
        "//*[contains(text(),'What do you want to talk about')]",
        "//*[contains(text(),'Talk about')]",
        "//div[contains(@class,'share-box')]",
        "//div[contains(@class,'artdeco-modal')]",
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

                    try:
                        safe_click(driver, el)
                    except Exception:
                        try:
                            el.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", el)

                    print("Clicked editor area using:", xpath)
                    time.sleep(2)
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def type_into_active_element(driver, caption):
    try:
        active = driver.switch_to.active_element
        try:
            print("Active element tag:", active.tag_name)
            print(
                "Active element outerHTML:",
                driver.execute_script("return arguments[0].outerHTML;", active)[:500]
            )
        except Exception:
            pass

        actions = ActionChains(driver)

        try:
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
            actions.send_keys(Keys.DELETE)
            actions.pause(0.3)
            actions.send_keys(caption)
            actions.perform()
            print("Typed using ActionChains")
            time.sleep(1)
            return True
        except Exception as e:
            print("ActionChains typing failed:", str(e))

        try:
            active.send_keys(caption)
            print("Typed using active element send_keys")
            time.sleep(1)
            return True
        except Exception as e:
            print("Active element send_keys failed:", str(e))

        return False

    except Exception as e:
        print("type_into_active_element error:", str(e))
        return False


def find_post_button(driver):
    xpath_candidates = [
        "//span[text()='Post']/ancestor::button[1]",
        "//button[.//span[text()='Post']]",
        "//button[contains(@aria-label,'Post')]",
        "//button[contains(@class,'share-actions')]",
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

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                try:
                    start_post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", start_post_button)

            print("LinkedIn 'Start a post' trigger clicked")

            # important: focus + ENTER
            try:
                driver.execute_script("arguments[0].focus();", start_post_button)
                time.sleep(0.5)
                ActionChains(driver).send_keys(Keys.ENTER).perform()
                print("Pressed ENTER on Start a post")
            except Exception as e:
                print("ENTER press failed:", str(e))

        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        time.sleep(3)

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        prompt = wait_for_prompt_text(driver, timeout=8)
        if not prompt:
            print("Prompt text not confidently detected, continuing with activation fallback")

        activated = activate_editor_v2(driver)
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

        typed = type_into_active_element(driver, post.caption)
        if not typed:
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
                try:
                    post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", post_button)

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