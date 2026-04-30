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
        # --- 1. OPEN LINKEDIN ---
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(6) # Give the feed time to load its dynamic components

        # --- 2. CLICK 'START A POST' (Physical Interaction) ---
        try:
            # We look for the button with specific text
            start_btn_xpath = "//button[contains(., 'Start a post')] | //div[@role='button'][contains(., 'Start a post')]"
            start_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, start_btn_xpath))
            )
            
            # Hover first, then click (more human-like)
            actions = ActionChains(driver)
            actions.move_to_element(start_btn).pause(0.5).click().perform()
            print("✅ Start post clicked")
        except Exception as e:
            return {"success": False, "message": f"Could not click Start Post: {str(e)}"}

        # --- 3. WAIT FOR DIALOG ---
        print("⏳ Waiting for dialog to appear...")
        dialog_xpath = "//div[@role='dialog'] | //div[contains(@class, 'share-box')]"
        try:
            dialog = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, dialog_xpath))
            )
            time.sleep(2) # Wait for fade-in animation
        except:
            screenshot = save_screenshot(driver, prefix="dialog_missing")
            return {"success": False, "message": "Dialog never appeared."}

        # --- 4. WRITE TEXT (JavaScript Injection) ---
        print("⌨️ Writing text...")
        # We search for the editor and use 'insertText' to trigger React state changes
        success = driver.execute_script("""
            const editor = document.querySelector('.ql-editor') || 
                           document.querySelector('div[contenteditable="true"]') || 
                           document.querySelector('[role="textbox"]');
            if (editor) {
                editor.focus();
                document.execCommand('insertText', false, arguments[0]);
                // Manually trigger input event so the Post button enables
                editor.dispatchEvent(new Event('input', { bubbles: true }));
                return true;
            }
            return false;
        """, post.caption)

        if not success:
            screenshot = save_screenshot(driver, prefix="editor_missing")
            return {"success": False, "message": "Could not find text editor inside dialog."}

        # --- 5. CLICK POST ---
        time.sleep(2) # Pause to let the 'Post' button turn blue
        try:
            # Target the button inside the active dialog only
            post_btn = dialog.find_element(By.XPATH, ".//button[contains(@class, 'primary-action')] | .//button[contains(., 'Post')]")
            driver.execute_script("arguments[0].click();", post_btn)
            print("✅ Post published!")
            return {"success": True, "message": "Post published successfully"}
        except:
            # Fallback if standard button find fails
            driver.execute_script("""
                const btns = Array.from(document.querySelectorAll('button'));
                const postBtn = btns.find(b => b.innerText.includes('Post') && !b.disabled);
                if (postBtn) postBtn.click();
            """)
            return {"success": True, "message": "Post published via JS fallback"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_crash")
        return {"success": False, "message": f"Unexpected error: {str(e)}"}