import os
import time

from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.logger import clean_log as log

from .utils import (
    wait_for_instagram_login,
    find_create_button,
    find_new_post_button,
    find_select_from_computer_button,
    find_file_input,
    click_next,
    find_caption_box,
    find_share_button,
    wait_for_caption_screen,
)

from automation_engine.common.logger import clean_log as log


def post_to_instagram(driver, post):
    """
    Publish a post on Instagram using Selenium automation.

    Flow:
    1. Get caption and media from post object
    2. Open Instagram login page
    3. Wait for user login
    4. Open Instagram home
    5. Click Create / New Post
    6. Upload media
    7. Click Next twice
    8. Enter caption
    9. Click Share
    """

    print("Calling Instagram automation...")

    try:
        caption = str(post.caption).strip()
        image_path = ""
        media = None

        # Resolve media path from post object
        if hasattr(post, "media") and post.media:
            try:
                media = post.media

                # If multiple images are provided
                if isinstance(media, list):
                    image_path = media[0] if media else ""

                # If single image path is provided
                elif isinstance(media, str):
                    image_path = media.strip()

                # Fallback for unsupported media format
                else:
                    image_path = ""

            except Exception:
                image_path = ""

        # Validate media file before starting Instagram flow
        if not image_path or not os.path.exists(image_path):
            return {
                "success": False,
                "message": f"Image file not found: {image_path}",
            }

        print("Opening Instagram login...")
        driver.get("https://www.instagram.com/accounts/login/")
        medium_pause()

        if not wait_for_instagram_login(driver, timeout=180):
            screenshot = save_screenshot(driver, prefix="insta_login_failed")
            return {
                "success": False,
                "message": f"Login not completed | {screenshot}",
            }

        print("Opening Instagram home...")
        driver.get("https://www.instagram.com/")
        log("📸 Instagram opened")
        medium_pause()

        create_btn = find_create_button(driver)
        log("➕ Clicking Create button...")
        if not create_btn:
            return {
                "success": False,
                "message": "Create button not found",
            }

        clicked = safe_click(driver, create_btn)

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
            return {
                "success": False,
                "message": "Create button click failed",
            }

        print("✅ Create button clicked")
        small_pause()

        print("Finding New Post button...")
        new_post_btn = find_new_post_button(driver)

        if new_post_btn:
            safe_click(driver, new_post_btn)
            print("✅ New Post button clicked")
            small_pause()

        print("Looking for 'Select from computer' button...")
        select_btn = find_select_from_computer_button(driver)

        if select_btn:
            safe_click(driver, select_btn)
            print("✅ Clicked 'Select from computer'")
            small_pause()

      
        file_input = find_file_input(driver, timeout=12)

        if not file_input:
            return {
                "success": False,
                "message": "Instagram file input not found",
            }

        media_files = media if isinstance(media, list) else [media]
        file_input.send_keys("\n".join(media_files))

        log("🖼 Uploading image...")
        medium_pause()

        
        if not click_next(driver):
            return {
                "success": False,
                "message": "First Next button not found or not working",
            }

        
        if not click_next(driver):
            return {
                "success": False,
                "message": "Second Next button not found or not working",
            }

       
        if not wait_for_caption_screen(driver, timeout=15):
            return {
                "success": False,
                "message": "Caption/share screen did not open",
            }

        caption_box = find_caption_box(driver)

        if not caption_box:
            return {
                "success": False,
                "message": "Caption box not found",
            }

        caption_box.click()
        time.sleep(1)

        typed = False

        try:
            type_like_human(caption_box, caption)
            typed = True
            log("✍️ Adding caption...")
        except Exception as e:
            print("⚠️ type_like_human failed:", str(e))

        if not typed:
            try:
                caption_box.send_keys(caption)
                typed = True
                print("✅ Caption entered using send_keys")
            except Exception as e:
                print("⚠️ send_keys failed:", str(e))

        if not typed:
            try:
                driver.execute_script(
                    """
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
                    """,
                    caption_box,
                    caption,
                )

                typed = True
                print("✅ Caption entered using JS fallback")

            except Exception as e:
                print("⚠️ JS caption fallback failed:", str(e))

        if not typed:
            screenshot = save_screenshot(driver, prefix="insta_caption_failed")
            return {
                "success": False,
                "message": f"Caption typing failed | {screenshot}",
            }
        log("📤 Sharing post...")
        share_btn = find_share_button(driver)

        if not share_btn:
            return {
                "success": False,
                "message": "Share button not found",
            }

        clicked = False

        try:
            clicked = safe_click(driver, share_btn)
        except Exception:
            pass

        if not clicked:
            try:
                share_btn.click()
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", share_btn)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {
                "success": False,
                "message": "Share button click failed",
            }

        print("✅ Share clicked")
        medium_pause()

        return {
            "success": True,
            "message": "Instagram post successful",
        }

    except Exception as e:
        print("❌ Instagram automation error:", str(e))

        return {
            "success": False,
            "message": str(e),
        }