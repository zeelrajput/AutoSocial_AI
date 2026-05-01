import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver):
    # 1. Try to scroll a bit to trigger lazy loading of the feed header
    driver.execute_script("window.scrollTo(0, 200);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")

    xpath_candidates = [
        "//button[contains(@class, 'share-box-feed-entry__trigger')]",
        "//button[contains(., 'Start a post')]",
        "//div[contains(@class, 'share-box-feed-entry')]//button",
        "//span[text()='Start a post']/ancestor::button",
    ]

    for xpath in xpath_candidates:
        try:
            # Increase wait for individual element visibility
            element = driver.find_element(By.XPATH, xpath)
            if element.is_displayed():
                print(f"✅ Found button with: {xpath}")
                return element
        except:
            continue
    return None

# =========================
# FIND REAL EDITOR (INSIDE DIALOG)
# =========================
def get_real_editor(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:

        dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
        print("Dialogs found:", len(dialogs))

        for dialog in dialogs:
            try:
                if not dialog.is_displayed():
                    continue

                editors = dialog.find_elements(By.XPATH, ".//div[@contenteditable='true']")
                print("Editors inside dialog:", len(editors))

                for editor in editors:
                    try:
                        if not editor.is_displayed():
                            continue

                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});",
                            editor
                        )

                        time.sleep(0.5)

                        try:
                            safe_click(driver, editor)
                        except:
                            driver.execute_script("arguments[0].click();", editor)

                        driver.execute_script("arguments[0].focus();", editor)

                        time.sleep(1)

                        print("✅ REAL LINKEDIN EDITOR FOUND")
                        return editor

                    except:
                        continue

            except:
                continue

        time.sleep(0.5)

    return None


# =========================
# TYPE TEXT
# =========================
def type_in_editor(driver, textbox, text):
    try:
        textbox.click()
    except:
        pass

    try:
        driver.execute_script("arguments[0].focus();", textbox)
    except:
        pass

    time.sleep(1)

    # 1. Normal typing
    try:
        textbox.send_keys(text)
        print("✅ Typed using send_keys")
        return True
    except:
        pass

    # 2. ActionChains
    try:
        ActionChains(driver).move_to_element(textbox).click().send_keys(text).perform()
        print("✅ Typed using ActionChains")
        return True
    except:
        pass

    # 3. JS fallback
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
        """, textbox, text)

        print("✅ Typed using JS fallback")
        return True
    except Exception as e:
        print("❌ Typing failed:", str(e))
        return False


# =========================
# FIND POST BUTTON
# =========================
def find_post_button(driver):
    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action')]",
        "//button[@aria-label='Post']",
        "//button[contains(@aria-label,'Post')]",
        "//span[text()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for btn in elements:
                if btn.is_displayed() and btn.is_enabled():
                    print("✅ Post button found using:", xpath)
                    return btn
        except:
            continue

    return None


# =========================
# MAIN FUNCTION
# =========================
def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)
        medium_pause()

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        # Step 1: Find Start Post
        start_post_button = find_start_post_button(driver)
        if not start_post_button:
                print(driver.page_source[:500]) # Print first 500 chars to see if you're actually logged in
                screenshot = save_screenshot(driver, prefix="debug_not_found")

                    # Step 2: Click Start Post
                    try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                start_post_button
            )
            time.sleep(1)

            driver.execute_script("arguments[0].click();", start_post_button)
            print("✅ Start post clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)} | Screenshot: {screenshot}"
            }

        time.sleep(3)

        # Step 3: Find Editor
        textbox = get_real_editor(driver, timeout=12)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        # Step 4: Type Text
        typed = type_in_editor(driver, textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        # Step 5: Click Post
        post_button = find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"Post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script("arguments[0].click();", post_button)
            print("✅ Post published")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"Post click failed: {str(e)} | Screenshot: {screenshot}"
            }

        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}