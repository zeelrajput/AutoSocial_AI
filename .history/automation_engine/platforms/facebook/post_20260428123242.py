import os
import time

from selenium.webdriver.common.by import By
from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.upload_helper import upload_file
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

        media_files = []

        if hasattr(post, "media") and post.media:
                media = post.media

                if isinstance(media, list):
                    media_files = media
                elif isinstance(media, str):
                    media_files = [media]
                elif hasattr(media, "path"):
                    media_files = [media.path]

                media_files = [
                    str(p).strip()
                    for p in media_files
                    if p and os.path.exists(str(p).strip())
                ]

        print("Facebook media files:", media_files)

        print("Opening Facebook...")
        driver.get("https://www.facebook.com/")
        medium_pause()

        if not wait_for_facebook_login(driver, timeout=180):
            screenshot = save_screenshot(driver, prefix="fb_login_failed")  # ✅ added
            return {"success": False, "message": f"Facebook login not completed | {screenshot}"}

        handle_facebook_security(driver)
        close_common_popups(driver)

        driver.get("https://www.facebook.com/")
        small_pause()
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
        medium_pause()
        close_common_popups(driver)

        # -------------------------------
        # 1. Upload image first (if any)
        # -------------------------------
        if media_files:
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
            medium_pause()

            print("Finding image file input...")
            file_input = find_file_input(driver, timeout=12)
            if not file_input:
                screenshot = save_screenshot(driver, prefix="fb_image_input_not_found")
                return {"success": False, "message": f"Image input not found | {screenshot}"}

            print("Using media path:", media_path)
            try:
                print("File input accept:", file_input.get_attribute("accept"))
            except Exception:
                pass

            file_input.send_keys("\n".join(media_files))
            print("✅ Facebook images uploaded:", media_files)

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
            small_pause()
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
            screenshot = save_screenshot(driver, prefix="fb_caption_failed")
            return {"success": False, "message": f"Caption typing failed | {screenshot}"}

        # -------------------------------
        # 3. Debug preview before post
        # -------------------------------
        if media_files:
            try:
                preview_images = driver.find_elements(By.XPATH, "//div[@role='dialog']//img")
                visible_previews = [img for img in preview_images if img.is_displayed()]
                print("Visible preview images before post:", len(visible_previews))

                if len(visible_previews) == 0:
                    screenshot = save_screenshot(driver, prefix="fb_preview_missing")
                    return {"success": False, "message": f"Image preview missing | {screenshot}"}
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
            screenshot = save_screenshot(driver, prefix="fb_post_click_failed")
            return {"success": False, "message": f"Post click failed | {screenshot}"}

        print("✅ Facebook post clicked")
        medium_pause()

        return {"success": True, "message": "Facebook post successful"}

    except Exception as e:
        print("❌ Facebook automation error:", str(e))
        return {"success": False, "message": str(e)}