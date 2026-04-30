import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause

# =========================
# THE "SLEDGEHAMMER" ACTIVATOR
# =========================
def get_activated_editor(driver):
    # 1. Force the browser to find the absolute first editable element on the whole page
    # This ignores nesting and Shadow DOM issues.
    script = """
    const editor = document.querySelector('.ql-editor') || 
                   document.querySelector('div[contenteditable="true"]') || 
                   document.querySelector('[role="textbox"]');
    if (editor) {
        editor.focus();
        return editor;
    }
    return null;
    """
    return driver.execute_script(script)

# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver):
    driver.execute_script("window.scrollTo(0, 0);")
    xpath_candidates = [
        "//button[contains(., 'Start a post')]",
        "//div[@role='button'][contains(., 'Start a post')]",
        "//button[contains(@class, 'share-box-feed-entry__trigger')]"
    ]
    for xpath in xpath_candidates:
        try:
            el = driver.find_element(By.XPATH, xpath)
            if el.is_displayed():
                return el
        except:
            continue
    return None
# =========================
# FIND REAL EDITOR (ENHANCED)
# =========================
def get_real_editor(driver, timeout=20):
    end_time = time.time() + timeout
    print("⏳ Waiting for post dialog to appear...")

    while time.time() < end_time:
        dialogs = driver.find_elements(
            By.XPATH,
            "//div[@role='dialog'] | //div[contains(@class,'artdeco-modal')] | //div[contains(@class,'share-box')]"
        )

        visible_dialogs = []
        for d in dialogs:
            try:
                if d.is_displayed():
                    rect = d.rect
                    area = rect.get("width", 0) * rect.get("height", 0)
                    visible_dialogs.append((area, d))
            except:
                pass

        # biggest visible dialog first = likely real composer
        visible_dialogs.sort(key=lambda x: x[0], reverse=True)

        print(f"🔍 Visible dialogs: {len(visible_dialogs)}")

        for idx, (_, dialog) in enumerate(visible_dialogs):
            try:
                print(f"➡️ Checking dialog {idx+1}, class={dialog.get_attribute('class')}")
            except:
                pass

            editor_selectors = [
                ".//div[contains(@class,'ql-editor')]",
                ".//div[@contenteditable='true']",
                ".//div[@role='textbox']",
                ".//*[@contenteditable='true']",
                ".//*[@role='textbox']",
                ".//p/ancestor::div[@contenteditable='true'][1]",
            ]

            for selector in editor_selectors:
                try:
                    editors = dialog.find_elements(By.XPATH, selector)
                    print(f"   Selector {selector} -> {len(editors)} matches")

                    for editor in editors:
                        try:
                            if editor.is_displayed():
                                driver.execute_script(
                                    "arguments[0].scrollIntoView({block:'center'});", editor
                                )
                                time.sleep(0.5)

                                try:
                                    editor.click()
                                except:
                                    driver.execute_script("arguments[0].click();", editor)

                                driver.execute_script("arguments[0].focus();", editor)
                                print(f"✅ REAL LINKEDIN EDITOR FOUND using: {selector}")
                                return editor
                        except:
                            continue
                except:
                    continue

            # fallback: click dialog body once, then try again
            try:
                driver.execute_script("arguments[0].click();", dialog)
                time.sleep(1)

                editors = dialog.find_elements(By.XPATH, ".//*[@contenteditable='true'] | .//*[@role='textbox']")
                for editor in editors:
                    if editor.is_displayed():
                        driver.execute_script("arguments[0].focus();", editor)
                        print("✅ Editor found after clicking dialog body")
                        return editor
            except:
                pass

        # global fallback
        try:
            global_editors = driver.find_elements(
                By.XPATH,
                "//*[@contenteditable='true'] | //*[@role='textbox'] | //div[contains(@class,'ql-editor')]"
            )
            print(f"🌍 Global editable candidates: {len(global_editors)}")

            for el in global_editors:
                try:
                    if el.is_displayed():
                        rect = el.rect
                        if rect.get("width", 0) > 50 and rect.get("height", 0) > 20:
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                            driver.execute_script("arguments[0].focus();", el)
                            print("✅ Found editor via global fallback")
                            return el
                except:
                    continue
        except:
            pass

        time.sleep(1.5)

    return None

# =========================
# TYPE TEXT
# =========================
def type_in_editor(driver, textbox, text):
    try:
        textbox.click()
        driver.execute_script("arguments[0].focus();", textbox)
    except:
        pass

    time.sleep(1)

    try:
        textbox.send_keys(text)
        print("✅ Typed using send_keys")
        return True
    except:
        pass

    try:
        ActionChains(driver).move_to_element(textbox).click().send_keys(text).perform()
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
                inputType: 'insertText',
                data: text
            }));
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
                    print(f"✅ Post button found using: {xpath}")
                    return btn
        except:
            continue
    return None

# Move this to the top of post.py
from django.utils import timezone 



def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)

        print("🖱️ Searching for Start Post trigger...")

        start_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Start a post')] | "
                "//div[@role='button'][contains(., 'Start a post')] | "
                "//button[contains(@class,'share-box-feed-entry__trigger')]"
            ))
        )

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_btn)
        time.sleep(1)

        try:
            start_btn.click()
        except:
            driver.execute_script("arguments[0].click();", start_btn)

        print("✅ Start post clicked")

        time.sleep(3)

        # important debug
        dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog'] | //div[contains(@class,'artdeco-modal')] | //div[contains(@class,'share-box')]")
        print(f"🔍 Dialogs found after click: {len(dialogs)}")

        print("⏳ Waiting for LinkedIn editor...")
        textbox = get_real_editor(driver, timeout=20)

        if not textbox:
            # stronger fallback
            try:
                textbox = driver.execute_script("""
                    const selectors = [
                        'div[role="dialog"] div.ql-editor',
                        'div[role="dialog"] div[contenteditable="true"]',
                        'div[role="dialog"] div[role="textbox"]',
                        'div.artdeco-modal div.ql-editor',
                        'div.artdeco-modal div[contenteditable="true"]',
                        'div.artdeco-modal div[role="textbox"]',
                        'div.share-box div.ql-editor',
                        'div.share-box div[contenteditable="true"]',
                        'div.share-box div[role="textbox"]',
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
            except:
                textbox = None

        if not textbox:
            save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": "Composer opened, but textbox not found."}

        print("✅ Textbox found")

        typed = type_in_editor(driver, textbox, str(post.caption).strip())

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