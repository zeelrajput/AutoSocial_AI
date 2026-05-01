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
# THE JS FILTER STRATEGY
# =========================
def get_editor_via_js(driver):
    """
    Finds the largest visible contenteditable div on the page.
    This bypasses XPath issues and targets the actual editor area.
    """
    script = """
    const editors = Array.from(document.querySelectorAll('div[contenteditable="true"], div.ql-editor, div[role="textbox"]'));
    const visibleEditor = editors.find(el => {
        const rect = el.getBoundingClientRect();
        // The main post box is usually large, icons/comment boxes are small
        return rect.width > 200 && rect.height > 50 && rect.top > 0;
    });
    if (visibleEditor) {
        visibleEditor.focus();
        return visibleEditor;
    }
    return null;
    """
    try:
        return driver.execute_script(script)
    except:
        return None
    
# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver):
    # Trigger lazy loading of the feed header
    driver.execute_script("window.scrollTo(0, 200);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")

    xpath_candidates = [
        "//button[contains(@class, 'share-box-feed-entry__trigger')]",
        "//button[contains(., 'Start a post')]",
        "//div[contains(@class, 'share-box-feed-entry')]//button",
        "//span[text()='Start a post']/ancestor::button[1]",
        "//div[@role='button' and contains(., 'Start a post')]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed() and el.is_enabled():
                    print(f"✅ REAL Start Post found using: {xpath}")
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

# =========================
# MAIN FUNCTION (REFINED CLICK)
# =========================
def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)
        
        # Step 1: Find Start Post
        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            return {"success": False, "message": "Start post button not found."}

        # Step 2: Click Start Post
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_post_button)
            time.sleep(1)
            
            # PHYSICAL CLICK via ActionChains is usually better for triggering modals
            ActionChains(driver).move_to_element(start_post_button).click().perform()
            print("✅ Start post clicked (ActionChains)")
        except:
            # JS Fallback if ActionChains fails
            driver.execute_script("arguments[0].click();", start_post_button)
            print("✅ Start post clicked (JS Fallback)")

        # IMPORTANT: Wait for animation to finish
        time.sleep(5) 

        # Step 3: Find Editor
        textbox = get_real_editor(driver, timeout=12)
        if not textbox:
            # One last try: Click the center of the modal area to force focus
            try:
                ActionChains(driver).move_by_offset(0, -100).click().perform()
                time.sleep(1)
                textbox = get_real_editor(driver, timeout=3)
            except:
                pass

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"}

        # Step 4: Type Text
        typed = type_in_editor(driver, textbox, post.caption)
        
        # Step 5: Post
        time.sleep(2)
        post_button = find_post_button(driver)
        if post_button:
            driver.execute_script("arguments[0].click();", post_button)
            return {"success": True, "message": "Post published"}
        
        return {"success": False, "message": "Could not find Post button after typing"}

    except Exception as e:
        return {"success": False, "message": str(e)}