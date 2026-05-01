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
def get_real_editor(driver, timeout=15):
    end_time = time.time() + timeout
    print("⏳ Waiting for post dialog to appear...")

    while time.time() < end_time:
        # 1. Search for the dialog first
        dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog'] | //div[contains(@class, 'share-box')] | //div[contains(@class, 'artdeco-modal')]")
        
        if dialogs:
            for dialog in dialogs:
                # 2. Broad Editor XPaths inside the dialog
                editor_selectors = [
                    ".//div[@role='textbox']",
                    ".//div[contains(@class, 'ql-editor')]",
                    ".//div[@contenteditable='true']",
                    ".//div[contains(@aria-label, 'Text editor')]"
                ]

                for selector in editor_selectors:
                    try:
                        editors = dialog.find_elements(By.XPATH, selector)
                        for editor in editors:
                            if editor.is_displayed():
                                # Bring to front and focus
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", editor)
                                time.sleep(1)
                                
                                # Use JS to force focus
                                driver.execute_script("arguments[0].focus();", editor)
                                try:
                                    editor.click() # Attempt physical click to trigger JS listeners
                                except:
                                    pass
                                    
                                print(f"✅ REAL LINKEDIN EDITOR FOUND using: {selector}")
                                return editor
                    except:
                        continue

        # 3. GLOBAL FALLBACK: If dialog search fails, search the entire page
        # Sometimes LinkedIn editors aren't properly nested in the DOM dialog object
        global_fallback = driver.find_elements(By.XPATH, "//div[@contenteditable='true' and @role='textbox']")
        if global_fallback:
            for gf in global_fallback:
                if gf.is_displayed():
                    print("✅ Found editor via Global Fallback")
                    return gf

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
                "//div[@role='button'][contains(., 'Start a post')]"
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

        print("⏳ Waiting for LinkedIn composer modal...")

        # Wait for dialog first
        dialog = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@role='dialog' and .//button] | "
                "//div[contains(@class,'artdeco-modal') and .//button]"
            ))
        )

        print("✅ Composer modal appeared")

        # Find editable area ONLY inside modal
        textbox = None
        editor_xpaths = [
            ".//div[contains(@class,'ql-editor') and @contenteditable='true']",
            ".//div[@role='textbox' and @contenteditable='true']",
            ".//div[@contenteditable='true']",
        ]

        for xpath in editor_xpaths:
            try:
                elems = dialog.find_elements(By.XPATH, xpath)
                for el in elems:
                    if el.is_displayed():
                        textbox = el
                        print(f"✅ Editor found using: {xpath}")
                        break
                if textbox:
                    break
            except:
                pass

        if not textbox:
            save_screenshot(driver, prefix="linkedin_no_textbox")
            return {"success": False, "message": "Composer opened, but textbox not found."}

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        time.sleep(1)

        # Strong focus
        try:
            textbox.click()
        except:
            driver.execute_script("arguments[0].click();", textbox)

        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(1)

        caption = str(post.caption).strip()

        typed = False

        # Method 1: normal send_keys
        try:
            textbox.clear()  # safe if supported
        except:
            pass

        try:
            textbox.send_keys(caption)
            typed = True
            print("✅ Typed using send_keys")
        except:
            pass

        # Method 2: ActionChains
        if not typed:
            try:
                ActionChains(driver).move_to_element(textbox).click(textbox).send_keys(caption).perform()
                typed = True
                print("✅ Typed using ActionChains")
            except:
                pass

        # Method 3: JS fallback for LinkedIn editor
        if not typed:
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
                """, textbox, caption)
                typed = True
                print("✅ Typed using JS fallback")
            except Exception as e:
                print("❌ JS typing failed:", str(e))

        if not typed:
            save_screenshot(driver, prefix="linkedin_typing_failed")
            return {"success": False, "message": "Textbox found, but typing failed."}

        time.sleep(3)

        # Find enabled Post button inside modal
        post_btn = None
        post_btn_xpaths = [
            ".//button[.//span[normalize-space()='Post'] and not(@disabled)]",
            ".//button[@aria-label='Post' and not(@disabled)]",
            ".//button[contains(., 'Post') and not(@disabled)]",
        ]

        for xpath in post_btn_xpaths:
            try:
                buttons = dialog.find_elements(By.XPATH, xpath)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        post_btn = btn
                        print(f"✅ Post button found using: {xpath}")
                        break
                if post_btn:
                    break
            except:
                pass

        if not post_btn:
            save_screenshot(driver, prefix="linkedin_post_disabled")
            return {"success": False, "message": "Text entered, but Post button not enabled."}

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", post_btn)
        time.sleep(1)

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