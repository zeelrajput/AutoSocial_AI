import time
import os
import io

from PIL import Image
import win32clipboard

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

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
                    return (
                        r.width > 10 &&
                        r.height > 10 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const selectors = [
                    "div[role='dialog']",
                    "[aria-label*='Start a post']",
                    "div[contenteditable='true']",
                    "div[role='textbox']",
                    ".ql-editor",
                    "[data-placeholder]"
                ];

                for (const sel of selectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;

                        const text = (
                            (el.innerText || '') + ' ' +
                            (el.textContent || '') + ' ' +
                            (el.getAttribute('aria-label') || '') + ' ' +
                            (el.getAttribute('data-placeholder') || '')
                        ).toLowerCase();

                        if (
                            text.includes('what do you want to talk about') ||
                            text.includes('talk about') ||
                            text.includes('post to anyone') ||
                            text.includes('create a post')
                        ) {
                            return true;
                        }
                    }
                }

                return false;
            """)
            if opened:
                return True
        except Exception as e:
            print(f"⚠️ Composer wait JS error: {e}")

        time.sleep(1)

    return False


def click_element_robustly(driver, element, name="Element"):
    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, element)),
        ("js_click", lambda: driver.execute_script("arguments[0].click();", element)),
        ("normal_click", lambda: element.click()),
    ]:
        try:
            result = action()
            if result is None or result is True:
                print(f"✅ {name} clicked using {action_name}")
                return True
        except Exception:
            continue
    return False


def type_caption(driver, textbox, caption):
    try:
        driver.execute_script("""
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
        """, textbox)
        time.sleep(1)
    except Exception:
        pass

    try:
        type_like_human(textbox, caption)
        print("✅ Caption entered using type_like_human")
        return True
    except Exception as e:
        print(f"⚠️ type_like_human failed: {e}")

    try:
        textbox.send_keys(caption)
        print("✅ Caption entered using send_keys")
        return True
    except Exception as e:
        print(f"⚠️ send_keys failed: {e}")

    try:
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();
            el.click();

            if (el.isContentEditable) {
                el.innerHTML = '';
                el.textContent = text;
            } else if ('value' in el) {
                el.value = text;
            }

            el.dispatchEvent(new InputEvent('input', {
                bubbles: true,
                cancelable: true,
                inputType: 'insertText',
                data: text
            }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, textbox, caption)
        print("✅ Caption entered using JS fallback")
        return True
    except Exception as e:
        print(f"⚠️ JS caption fallback failed: {e}")

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

        ActionChains(driver) \
            .move_to_element(textbox) \
            .click(textbox) \
            .key_down(Keys.CONTROL) \
            .send_keys("v") \
            .key_up(Keys.CONTROL) \
            .perform()

        print("✅ Image pasted from clipboard")
        time.sleep(6)

        pasted = driver.execute_script("""
            const imgs = Array.from(document.querySelectorAll("img"));
            return imgs.some(img => {
                const r = img.getBoundingClientRect();
                const s = window.getComputedStyle(img);
                return (
                    r.width > 40 &&
                    r.height > 40 &&
                    s.display !== 'none' &&
                    s.visibility !== 'hidden' &&
                    s.opacity !== '0'
                );
            });
        """)
        print("🧾 Image preview detected:", pasted)
        return pasted
    except Exception as e:
        print("⚠️ Clipboard paste failed:", str(e))
        return False


def post_to_linkedin(driver, post):
    print("🚀 Starting LinkedIn automation...")

    try:
        caption = str(getattr(post, "caption", "")).strip()

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        if not wait_for_linkedin_login(driver, timeout=180):
            return {"success": False, "message": "Login timeout"}

        close_common_popups(driver)

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        close_common_popups(driver)

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        start_btn = find_start_post_button(driver, timeout=15)
        if not start_btn:
            return {"success": False, "message": "Start Post button not found"}

        if not click_element_robustly(driver, start_btn, "Start Post"):
            return {"success": False, "message": "Could not click Start Post"}

        if not wait_for_composer_open(driver):
            print("⚠️ Composer verification failed, trying textbox anyway...")

        textbox = find_linkedin_textbox(driver, timeout=20)
        if not textbox:
            return {"success": False, "message": "Textbox not found"}

        if not type_caption(driver, textbox, caption):
            return {"success": False, "message": "Caption typing failed"}

        media_field = getattr(post, "media", None)
        print("🧾 media field:", media_field)

        image_path = None
        if media_field:
            try:
                image_path = media_field.path
            except Exception:
                image_path = str(media_field)

        print("🧾 resolved image_path:", image_path)

        if image_path:
            abs_path = os.path.abspath(str(image_path))
            print("📸 Uploading:", abs_path)
            print("🧾 image exists:", os.path.exists(abs_path))

            if not os.path.exists(abs_path):
                return {"success": False, "message": f"Image file not found: {abs_path}"}

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
                    time.sleep(5)
                except Exception as e:
                    print("⚠️ File input upload failed:", str(e))
                    print("⚠️ Trying clipboard fallback...")
                    if not paste_image_from_clipboard(driver, textbox, abs_path):
                        return {"success": False, "message": f"Image upload failed: {str(e)}"}
            else:
                print("⚠️ File input not found → trying clipboard fallback...")
                if not paste_image_from_clipboard(driver, textbox, abs_path):
                    return {"success": False, "message": "LinkedIn image upload failed"}

        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15, textbox=textbox)
        if not post_btn:
            return {"success": False, "message": "Post button not found"}

        if not click_element_robustly(driver, post_btn, "Post Button"):
            return {"success": False, "message": "Failed to click Post button"}

        time.sleep(5)
        return {"success": True, "message": "Post submitted successfully"}

    except Exception as e:
        print(f"❌ Automation Error: {str(e)}")
        return {"success": False, "message": str(e)}