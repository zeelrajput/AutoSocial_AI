import os
import time

from selenium.webdriver.common.by import By
from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.file_helper import upload_file
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_facebook_login,
    close_common_popups,
    handle_facebook_security,
    find_create_post_button,
    find_textbox,
    find_photo_video_button,
    find_file_input,
    find_post_button,
    wait_for_uploaded_image_ready,
)


def post_to_facebook(driver, post):
    print("Calling Facebook automation...")
    try:
        caption = str(post.caption or "").strip()

        image_path = ""
        if hasattr(post, "media") and post.media:
            try:
                image_path = post.media.path
            except Exception:
                image_path = ""

        print("Opening Facebook...")
        driver.get("https://www.facebook.com/")
        time.sleep(4)

        if not wait_for_facebook_login(driver, timeout=180):
            return {"success": False, "message": "Facebook login not completed"}

        handle_facebook_security(driver)
        close_common_popups(driver)

        driver.get("https://www.facebook.com/")
        time.sleep(3)
        close_common_popups(driver)

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        print("Finding Create Post button...")
        create_btn = find_create_post_button(driver, timeout=15)
        if not create_btn:
            return {"success": False, "message": "Create post button not found"}

        clicked = False
        try:
            clicked = safe_click(driver, create_btn)
        except Exception:
            pass

        if not clicked:
            try:
                create_btn.click()
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", create_btn)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "Create post button click failed"}

        print("✅ Create post clicked")
        time.sleep(3)
        close_common_popups(driver)

        # -------------------------------
        # 1. Upload image first (if any)
        # -------------------------------
        if image_path and os.path.exists(image_path):
            print("Finding Photo/Video button...")
            photo_btn = find_photo_video_button(driver, timeout=10)
            if not photo_btn:
                return {"success": False, "message": "Facebook Photo/Video button not found"}

            clicked = False

            try:
                clicked = safe_click(driver, photo_btn)
            except Exception:
                pass

            if not clicked:
                try:
                    photo_btn.click()
                    clicked = True
                except Exception:
                    pass

            if not clicked:
                try:
                    driver.execute_script("arguments[0].click();", photo_btn)
                    clicked = True
                except Exception:
                    pass

            if not clicked:
                return {"success": False, "message": "Facebook Photo/Video click failed"}

            print("✅ Photo/Video clicked")
            time.sleep(3)

            print("Finding image file input...")
            file_input = find_file_input(driver, timeout=12)
            if not file_input:
                return {"success": False, "message": "Facebook image file input not found"}

            print("Using media path:", image_path)
            try:
                print("File input accept:", file_input.get_attribute("accept"))
            except Exception:
                pass

            file_input.send_keys(image_path)
            print("✅ Image uploaded")

            print("Waiting for Facebook image to finish processing...")
            if not wait_for_uploaded_image_ready(driver, timeout=25):
                return {"success": False, "message": "Facebook image preview/upload not ready"}

            time.sleep(2)

       
         # -------------------------------
        # 2. Type caption after image
        # -------------------------------
        time.sleep(2)
        close_common_popups(driver)

        print("Finding textbox after image upload...")
        textbox = find_textbox(driver, timeout=15)
        if not textbox:
            return {"success": False, "message": "Facebook textbox not found"}

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        except Exception:
            pass

        try:
            textbox.click()
            time.sleep(1)
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", textbox)
                time.sleep(1)
            except Exception:
                pass

        typed = False

        try:
            type_like_human(textbox, caption)
            typed = True
            print("✅ Caption entered using type_like_human")
        except Exception as e:
            print("⚠️ type_like_human failed:", str(e))

        if not typed:
            try:
                textbox.send_keys(caption)
                typed = True
                print("✅ Caption entered using send_keys")
            except Exception as e:
                print("⚠️ send_keys failed:", str(e))

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];
                    el.focus();

                    if (el.tagName === 'TEXTAREA' || 'value' in el) {
                        el.value = text;
                    } else {
                        el.textContent = text;
                        el.innerHTML = text;
                    }

                    el.dispatchEvent(new InputEvent('input', {
                        bubbles: true,
                        cancelable: true,
                        inputType: 'insertText',
                        data: text
                    }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, textbox, caption)
                typed = True
                print("✅ Caption entered using JS fallback")
            except Exception as e:
                print("⚠️ JS caption fallback failed:", str(e))

        if not typed:
            return {"success": False, "message": "Facebook caption typing failed"}

        # -------------------------------
        # 3. Debug preview before post
        # -------------------------------
        if image_path and os.path.exists(image_path):
            try:
                preview_images = driver.find_elements(By.XPATH, "//div[@role='dialog']//img")
                visible_previews = [img for img in preview_images if img.is_displayed()]
                print("Visible preview images before post:", len(visible_previews))

                if len(visible_previews) == 0:
                    return {"success": False, "message": "Facebook image preview missing before post"}
            except Exception as e:
                print("⚠️ Preview image debug failed:", str(e))
                return {"success": False, "message": f"Facebook preview check failed: {str(e)}"}

        # -------------------------------
        # 4. Click Post
        # -------------------------------
        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15)
        if not post_btn:
            return {"success": False, "message": "Facebook post button not found"}

        clicked = False
        try:
            clicked = safe_click(driver, post_btn)
        except Exception:
            pass

        if not clicked:
            try:
                post_btn.click()
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", post_btn)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "Facebook post button click failed"}

        print("✅ Facebook post clicked")
        time.sleep(8)

        return {"success": True, "message": "Facebook post successful"}

    except Exception as e:
        print("❌ Facebook automation error:", str(e))
        return {"success": False, "message": str(e)}