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

        # --- STEP 1: FORCE THE MODAL OPEN ---
        print("🖱️ Targeting Start Post trigger...")
        # We find the container that holds the 'Start a post' text
        trigger_xpath = "//button[contains(@class, 'share-box-feed-entry__trigger')] | //span[text()='Start a post']/.."
        
        try:
            trigger = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, trigger_xpath))
            )
            # Strategy: Move mouse to the button and click the middle
            actions = ActionChains(driver)
            actions.move_to_element(trigger).click().perform()
            print("✅ Start post clicked (ActionChains)")
        except:
            # Fallback: JavaScript click directly on the span text
            driver.execute_script("document.evaluate(\"//span[text()='Start a post']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();")
            print("✅ Start post clicked (JS Fallback)")
        
        time.sleep(5) # Give LinkedIn a generous 5 seconds to load the React modal

        # --- STEP 2: AGGRESSIVE EDITOR SEARCH ---
        print("⏳ Searching for editable area...")
        # We check for the 'ql-editor' which is the specific class for the LinkedIn/Quill editor
        editor = None
        for i in range(10):
            # Try to find by class name directly
            editors = driver.find_elements(By.CLASS_NAME, "ql-editor")
            if not editors:
                # Try to find any contenteditable div
                editors = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
            
            for el in editors:
                if el.is_displayed():
                    editor = el
                    break
            
            if editor: break
            print(f"...Retry {i+1}: Editor not ready...")
            time.sleep(1.5)

        if not editor:
            screenshot = save_screenshot(driver, prefix="modal_fail_debug")
            return {"success": False, "message": f"Editor failed to appear. Check screenshot: {screenshot}"}

        # --- STEP 3: TEXT INJECTION & STATE TRIGGER ---
        print("⌨️ Injecting text...")
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];
            el.focus();
            // Clear existing text
            el.innerHTML = '';
            // Insert new text
            document.execCommand('insertText', false, text);
            // Fire 'input' event so the 'Post' button enables
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, editor, post.caption)
        
        time.sleep(2)

        # --- STEP 4: CLICK POST ---
        try:
            # The button only enables after text is injected
            post_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'share-actions__primary-action')] | //button[span[text()='Post']]"))
            )
            driver.execute_script("arguments[0].click();", post_btn)
            print("✅ Post published!")
            return {"success": True, "message": "Post published successfully"}
        except:
            # Last resort JS click for the button
            driver.execute_script("document.querySelector('.share-actions__primary-action').click();")
            return {"success": True, "message": "Post published via JS fallback"}

    except Exception as e:
        return {"success": False, "message": f"Automation Error: {str(e)}"}