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
        time.sleep(7) # Increased wait for 2026 feed weights

        # 1. FIND AND PHYSICALLY CLICK 'START A POST'
        print("🖱️ Performing trusted click on Start Post...")
        start_btn_xpath = "//button[contains(., 'Start a post')] | //div[@role='button'][contains(., 'Start a post')]"
        try:
            start_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, start_btn_xpath))
            )
            # Ensure it's in view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_btn)
            time.sleep(1)
            
            # PHYSICAL SEQUENCE: Move, Press, Release
            actions = ActionChains(driver)
            actions.move_to_element(start_btn).click_and_hold().pause(0.2).release().perform()
            print("✅ Start post clicked (Physical Sequence)")
        except:
            return {"success": False, "message": "Could not interact with Start Post button"}

        # 2. GLOBAL SEARCH FOR EDITOR
        print("⏳ Scanning for editor initialization...")
        textbox = None
        for _ in range(12): # 12 second total wait
            # Try to find the editor by class, role, or contenteditable
            found_els = driver.find_elements(By.CSS_SELECTOR, ".ql-editor, [contenteditable='true'], [role='textbox']")
            for el in found_els:
                if el.is_displayed():
                    textbox = el
                    break
            if textbox: break
            time.sleep(1)

        if not textbox:
            # LAST DITCH: Refresh if not found (sometimes LinkedIn stalls)
            screenshot = save_screenshot(driver, prefix="editor_not_found")
            return {"success": False, "message": f"Editor failed to appear. Screenshot: {screenshot}"}

        print("✅ Editor detected")

        # 3. TYPING VIA INPUT EMULATION
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];
            el.focus();
            // This is the specific way to bypass 2026 LinkedIn Quill blocks
            const dataTransfer = new DataTransfer();
            dataTransfer.setData('text/plain', text);
            el.dispatchEvent(new ClipboardEvent('paste', {
                clipboardData: dataTransfer,
                bubbles: true,
                cancelable: true
            }));
            // If paste fails, fallback to insertText
            if (el.innerText.length < 2) {
                document.execCommand('insertText', false, text);
            }
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, textbox, post.caption)
        
        print("✅ Text entered")
        time.sleep(2)

        # 4. FIND AND CLICK POST
        try:
            # Target the button that isn't disabled
            post_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'share-actions__primary-action')] | //button[span[text()='Post']]")
            driver.execute_script("arguments[0].click();", post_btn)
            print("✅ Post published!")
            return {"success": True, "message": "Post published successfully"}
        except:
            # JS Fallback for the Post button
            driver.execute_script("""
                const b = Array.from(document.querySelectorAll('button')).find(el => el.textContent.trim() === 'Post' && !el.disabled);
                if (b) b.click();
            """)
            return {"success": True, "message": "Post published via JS Fallback"}

    except Exception as e:
        return {"success": False, "message": f"Critical Error: {str(e)}"}