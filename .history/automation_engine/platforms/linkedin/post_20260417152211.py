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

def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(6)

        start_btn = find_start_post_button(driver)
        if not start_btn:
            return {"success": False, "message": "Start Post button not found"}

        # --- STEP 2: RELIABLE CLICK ---
        print("Attempting physical click on Start Post...")
        try:
            # Physical interaction is harder for LinkedIn to ignore
            ActionChains(driver).move_to_element(start_btn).click().perform()
        except:
            driver.execute_script("arguments[0].click();", start_btn)
        
        # --- STEP 3: WAIT FOR DIALOG (CRITICAL) ---
        print("⏳ Waiting for dialog to inject into DOM...")
        try:
            # Wait up to 10 seconds for the dialog to actually exist
            dialog_xpath = "//div[@role='dialog'] | //div[contains(@class, 'share-box')] | //div[contains(@class, 'artdeco-modal')]"
            dialog = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, dialog_xpath))
            )
            print("✅ Dialog detected in DOM")
            time.sleep(2) # Wait for animation
        except:
            screenshot = save_screenshot(driver, prefix="no_dialog_detected")
            return {"success": False, "message": "LinkedIn dialog never opened. Check screenshot."}

        # --- STEP 4: ACTIVATE & TYPE ---
        # Now that we KNOW the dialog is there, we find the editor
        textbox = driver.execute_script("""
            const editor = document.querySelector('.ql-editor') || 
                           document.querySelector('div[contenteditable="true"]') || 
                           document.querySelector('[role="textbox"]');
            if (editor) {
                editor.focus();
                return editor;
            }
            return null;
        """)
        
        if not textbox:
            # Last ditch effort: Click the middle of the dialog we just found
            ActionChains(driver).move_to_element_with_offset(dialog, 0, 80).click().perform()
            time.sleep(1)
            textbox = get_activated_editor(driver)

        if not textbox:
            return {"success": False, "message": "Could not find editor inside dialog."}

        print("✅ Editor active. Entering text...")
        driver.execute_script("""
            arguments[0].focus();
            document.execCommand('insertText', false, arguments[1]);
        """, textbox, post.caption)
        
        # --- STEP 5: POST ---
        time.sleep(3) 
        # Target the button inside the dialog specifically
        post_btn = dialog.find_element(By.XPATH, ".//button[contains(@class, 'share-actions__primary-action')] | .//button[contains(., 'Post')]")
        driver.execute_script("arguments[0].click();", post_btn)
        
        return {"success": True, "message": "Post published successfully!"}

    except Exception as e:
        return {"success": False, "message": f"Final Error: {str(e)}"}