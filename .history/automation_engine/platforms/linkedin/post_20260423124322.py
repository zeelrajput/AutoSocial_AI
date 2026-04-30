import time
import os
import io
from PIL import Image
import win32clipboard
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# Assuming these helpers exist in your environment
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_post_button,
    find_image_input,
    find_photo_button,
)

def wait_for_composer_open(driver, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            opened = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (r.width > 10 && r.height > 10 && s.display !== 'none' && 
                            s.visibility !== 'hidden' && s.opacity !== '0');
                }
                const selectors = ["div[role='dialog']", "[aria-label*='Start a post']", "div[contenteditable='true']"];
                for (const sel of selectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;
                        const text = (el.innerText + ' ' + el.getAttribute('aria-label') + ' ' + el.getAttribute('data-placeholder')).toLowerCase();
                        if (text.includes('talk about') || text.includes('post to anyone') || text.includes('create a post')) return true;
                    }
                }
                return false;
            """)
            if opened: return True
        except Exception as e:
            print(f"⚠️ Composer wait JS error: {e}")
        time.sleep(1)
    return False

def click_element_robustly(driver, element, name="Element"):
    """Generic robust clicker to replace repetitive try-except blocks."""
    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, element)),
        ("js_click", lambda: driver.execute_script("arguments[0].click();", element)),
        ("normal_click", lambda: element.click()),
    ]:
        try:
            action()
            print(f"✅ {name} clicked using {action_name}")
            return True
        except Exception:
            continue
    return False

def type_caption(driver, textbox, caption):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", textbox)
        time.sleep(1)
        type_like_human(textbox, caption)
        print("✅ Caption entered")
        return True
    except Exception as e:
        print(f"⚠️ Typing failed, trying send_keys: {e}")
        try:
            textbox.send_keys(caption)
            return True
        except:
            return False
        
def copy_image_to_clipboard(image_path):
    image = Image.open(image_path)

    if image.mode != "RGB":
        image = image.convert("RGB")

    output = io.BytesIO()
    image.save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


def paste_image_from_clipboard(driver, textbox, image_path):
    try:
        copy_image_to_clipboard(image_path)
        print("✅ Image copied to clipboard")

        driver.execute_script("""
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
        """, textbox)

        time.sleep(1)

        ActionChains(driver)\
            .move_to_element(textbox)\
            .click(textbox)\
            .key_down(Keys.CONTROL)\
            .send_keys("v")\
            .key_up(Keys.CONTROL)\
            .perform()

        print("✅ Image pasted from clipboard")
        time.sleep(3)

        return True

    except Exception as e:
        print("⚠️ Clipboard paste failed:", str(e))
        return False



def post_to_linkedin(driver, post):
    print("🚀 Starting LinkedIn automation...")
    try:
        caption = str(getattr(post, 'caption', "")).strip()
        
        driver.get("https://www.linkedin.com/feed/")
        if not wait_for_linkedin_login(driver, timeout=180):
            return {"success": False, "message": "Login timeout"}

        close_common_popups(driver)
        
        start_btn = find_start_post_button(driver, timeout=15)
        if not start_btn or not click_element_robustly(driver, start_btn, "Start Post"):
            return {"success": False, "message": "Could not click Start Post"}

        if not wait_for_composer_open(driver):
            print("⚠️ Composer verification failed, attempting to find textbox anyway...")

        textbox = find_linkedin_textbox(driver, timeout=15)
        if not textbox:
            return {"success": False, "message": "Textbox not found"}

        type_caption(driver, textbox, caption)

        # Media Handling
        image_path = getattr(post, 'media', None)
        if hasattr(image_path, 'path'):
            image_path = image_path.path  # Handle object or string

        if image_path and os.path.exists(str(image_path)):
            abs_path = os.path.abspath(str(image_path))
            print(f"📸 Uploading: {abs_path}")

            file_input = find_image_input(driver, timeout=5)

            if not file_input:
                photo_btn = find_photo_button(driver, timeout=5)
                if photo_btn:
                    click_element_robustly(driver, photo_btn, "Photo Button")
                    time.sleep(3)
                    file_input = find_image_input(driver, timeout=10)

            if file_input:
                try:
                    file_input.send_keys(abs_path)
                    print("✅ Image file path sent")
                    time.sleep(3)
                except Exception as e:
                    print("⚠️ File input failed → trying clipboard fallback:", str(e))
                    if not paste_image_from_clipboard(driver, textbox, abs_path):
                        return {"success": False, "message": "Image upload failed"}
            else:
                print("⚠️ No file input found → trying clipboard fallback")
                if not paste_image_from_clipboard(driver, textbox, abs_path):
                    return {"success": False, "message": "LinkedIn image upload failed"}

            print("🔄 Re-finding Post button after image upload...")

          clicked_post = False

        for i in range(5):
            try:
                post_btn = find_post_button(driver, timeout=5, textbox=textbox)

                if post_btn:
                    print(f"✅ Post button found on retry {i+1}")

                    if click_element_robustly(driver, post_btn, "Post Button"):
                        print("✅ Post button clicked")
                        clicked_post = True
                        break

            except Exception as e:
                print(f"⚠️ Retry {i+1} failed: {str(e)}")

            time.sleep(2)

        if not clicked_post:
            return {"success": False, "message": "Failed to click the final Post button"}

        # Verification
        time.sleep(5)
        return {"success": True, "message": "Post submitted successfully"}

    except Exception as e:
        print(f"❌ Automation Error: {str(e)}")
        return {"success": False, "message": str(e)}