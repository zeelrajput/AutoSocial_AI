import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.screenshot_helper import save_screenshot
from django.utils import timezone


# =========================
# CHECK IF COMPOSER / EDITOR REALLY OPENED
# =========================
def linkedin_editor_or_modal_exists(driver):
    try:
        return driver.execute_script("""
            const selectors = [
                'div[role="dialog"]',
                'div.artdeco-modal',
                'div.share-box',
                'div[contenteditable="true"]',
                'div[role="textbox"]',
                '.ql-editor'
            ];

            for (const sel of selectors) {
                const els = document.querySelectorAll(sel);
                for (const el of els) {
                    const r = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);

                    if (
                        r.width > 50 &&
                        r.height > 20 &&
                        style.display !== 'none' &&
                        style.visibility !== 'hidden'
                    ) {
                        return true;
                    }
                }
            }
            return false;
        """)
    except:
        return False


# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver, timeout=20):
    xpath_candidates = [
        "//button[contains(., 'Start a post')]",
        "//div[@role='button'][contains(., 'Start a post')]",
        "//button[contains(@class, 'share-box-feed-entry__trigger')]",
        "//div[contains(@class, 'share-box-feed-entry__trigger')]",
        "//span[contains(., 'Start a post')]/ancestor::button[1]",
        "//span[contains(., 'Start a post')]/ancestor::div[@role='button'][1]"
    ]

    for xpath in xpath_candidates:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if element.is_displayed():
                print(f"✅ Start post button found using: {xpath}")
                return element
        except:
            continue

    return None


# =========================
# ACTIVATE START POST STRONGLY
# =========================
def activate_start_post(driver, start_btn):
    print("⚡ Activating Start post...")

    attempts = [
        "normal_click",
        "js_click",
        "action_click",
        "enter_key",
        "space_key",
        "child_click_js"
    ]

    for attempt in attempts:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_btn)
            time.sleep(1)

            if attempt == "normal_click":
                start_btn.click()

            elif attempt == "js_click":
                driver.execute_script("arguments[0].click();", start_btn)

            elif attempt == "action_click":
                ActionChains(driver).move_to_element(start_btn).pause(0.5).click().perform()

            elif attempt == "enter_key":
                start_btn.send_keys(Keys.ENTER)

            elif attempt == "space_key":
                start_btn.send_keys(Keys.SPACE)

            elif attempt == "child_click_js":
                driver.execute_script("""
                    const el = arguments[0];
                    const child = el.querySelector('span, div');
                    if (child) {
                        child.click();
                    } else {
                        el.click();
                    }
                """, start_btn)

            print(f"✅ Start post activation tried with: {attempt}")
            time.sleep(2)

            if linkedin_editor_or_modal_exists(driver):
                print("✅ Composer/editor detected after activation")
                return True

        except Exception as e:
            print(f"❌ Activation method failed: {attempt} -> {str(e)}")

    return False


# =========================
# FIND REAL LINKEDIN EDITOR
# =========================
def get_real_editor(driver, timeout=20):
    end_time = time.time() + timeout
    print("⏳ Waiting for LinkedIn editor...")

    while time.time() < end_time:
        try:
            editor = driver.execute_script("""
                const selectors = [
                    'div[role="dialog"] .ql-editor',
                    'div[role="dialog"] div[contenteditable="true"]',
                    'div[role="dialog"] div[role="textbox"]',

                    'div.artdeco-modal .ql-editor',
                    'div.artdeco-modal div[contenteditable="true"]',
                    'div.artdeco-modal div[role="textbox"]',

                    '.share-box .ql-editor',
                    '.share-box div[contenteditable="true"]',
                    '.share-box div[role="textbox"]',

                    '.ql-editor',
                    'div[contenteditable="true"]',
                    'div[role="textbox"]'
                ];

                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const r = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);

                        if (
                            r.width > 50 &&
                            r.height > 20 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden'
                        ) {
                            el.scrollIntoView({block:'center'});
                            el.focus();
                            return el;
                        }
                    }
                }
                return null;
            """)

            if editor:
                print("✅ Editor found")
                return editor

        except Exception as e:
            print(f"❌ Editor search error: {str(e)}")

        time.sleep(1)

    return None


# =========================
# TYPE TEXT INTO EDITOR
# =========================
def type_in_editor(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(1)
    except:
        pass

    try:
        textbox.click()
        time.sleep(0.5)
        textbox.send_keys(text)
        print("✅ Typed using send_keys")
        return True
    except:
        pass

    try:
        ActionChains(driver).move_to_element(textbox).click().pause(0.5).send_keys(text).perform()
        print("✅ Typed using ActionChains")
        return True
    except:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();
            el.innerHTML = '';
            el.textContent = text;

            el.dispatchEvent(new InputEvent('input', {
                bubbles: true,
                cancelable: true,
                inputType: 'insertText',
                data: text
            }));

            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: ' ' }));
            el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: ' ' }));
        """, textbox, text)

        print("✅ Typed using JS fallback")
        return True

    except Exception as e:
        print(f"❌ Typing failed: {str(e)}")
        return False


# =========================
# FIND POST BUTTON
# =========================
def find_post_button(driver):
    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action') and not(@disabled)]",
        "//button[@aria-label='Post' and not(@disabled)]",
        "//button[contains(@aria-label,'Post') and not(@disabled)]",
        "//span[normalize-space()='Post']/ancestor::button[1][not(@disabled)]",
        "//button[contains(., 'Post') and not(@disabled)]"
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for btn in elements:
                if btn.is_displayed() and btn.is_enabled():
                    print(f"✅ Post button found using: {xpath}")
                    return btn
        except:
            continue

    return None


# =========================
# MAIN LINKEDIN POST FUNCTION
# =========================
def post_to_linkedin(driver, post):
    try:
        print("Calling LinkedIn automation...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)

        print("🖱️ Searching for Start Post trigger...")
        start_btn = find_start_post_button(driver, timeout=20)

        if not start_btn:
            save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {"success": False, "message": "Start post button not found."}

        opened = activate_start_post(driver, start_btn)

        if not opened:
            save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {"success": False, "message": "Start post was clicked, but composer never opened."}

        textbox = get_real_editor(driver, timeout=15)

        if not textbox:
            save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": "Composer opened, but textbox not found."}

        caption = str(post.caption).strip()
        typed = type_in_editor(driver, textbox, caption)

        if not typed:
            save_screenshot(driver, prefix="linkedin_typing_failed")
            return {"success": False, "message": "Textbox found, but typing failed."}

        print("✅ Caption entered")
        time.sleep(3)

        post_btn = find_post_button(driver)

        if not post_btn:
            save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {"success": False, "message": "Text entered, but Post button not found or disabled."}

        try:
            post_btn.click()
        except:
            driver.execute_script("arguments[0].click();", post_btn)

        print("✅ Post button clicked")
        time.sleep(5)

        return {"success": True, "message": "Post published successfully"}

    except Exception as e:
        save_screenshot(driver, prefix="linkedin_error")
        return {"success": False, "message": f"Automation Error: {str(e)}"}