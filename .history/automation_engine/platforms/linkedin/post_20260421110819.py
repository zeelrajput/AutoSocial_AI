import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot


def post_to_linkedin(driver, post):
    try:
        profile_url = "https://www.linkedin.com/in/zeel-rajput-25010136b/"
        caption = str(post.caption).strip()

        driver.get(profile_url)
        time.sleep(6)

        # Scroll to Activity section
        activity_section = driver.find_element(
            By.XPATH,
            "//section[.//*[contains(normalize-space(),'Activity')]]"
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", activity_section)
        time.sleep(2)

        # Click Create a post button inside Activity
        create_post_btn = activity_section.find_element(
            By.XPATH,
            ".//button[contains(., 'Create a post')]"
        )

        clicked = safe_click(driver, create_post_btn)
        if not clicked:
            driver.execute_script("arguments[0].click();", create_post_btn)

        print("Clicked 'Create a post' from Activity section")
        time.sleep(3)

        # Find composer textbox
        textbox_candidates = driver.find_elements(
            By.XPATH,
            "//div[@role='dialog']//div[@contenteditable='true'] | "
            "//div[@role='dialog']//div[@role='textbox'] | "
            "//div[@role='dialog']//textarea"
        )

        textbox = None
        for el in textbox_candidates:
            try:
                if el.is_displayed():
                    textbox = el
                    break
            except Exception:
                continue

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"Textbox not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
            driver.execute_script("arguments[0].focus();", textbox)
            time.sleep(1)
            textbox.click()
        except Exception:
            pass

        typed = False

        try:
            textbox.send_keys(caption)
            print("Caption typed using send_keys")
            typed = True
        except Exception:
            pass

        if not typed:
            try:
                ActionChains(driver).move_to_element(textbox).click().pause(0.5).send_keys(caption).perform()
                print("Caption typed using ActionChains")
                typed = True
            except Exception:
                pass

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];

                    el.focus();

                    if (el.tagName === 'TEXTAREA' || 'value' in el) {
                        el.value = text;
                    } else {
                        el.innerHTML = '';
                        el.textContent = text;
                    }

                    el.dispatchEvent(new InputEvent('input', {
                        bubbles: true,
                        cancelable: true,
                        inputType: 'insertText',
                        data: text
                    }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, textbox, caption)
                print("Caption typed using JS fallback")
                typed = True
            except Exception:
                pass

        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)

        # Find Post button
        post_buttons = driver.find_elements(
            By.XPATH,
            "//div[@role='dialog']//button[@aria-label='Post' or contains(@aria-label,'Post') or .//span[normalize-space()='Post']]"
        )

        post_btn = None
        for btn in post_buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    post_btn = btn
                    break
            except Exception:
                continue

        if not post_btn:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"Post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, post_btn)
        if not clicked:
            driver.execute_script("arguments[0].click();", post_btn)

        print("Post published on LinkedIn")
        time.sleep(5)

        return {
            "success": True,
            "message": "Post published on LinkedIn"
        }

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }