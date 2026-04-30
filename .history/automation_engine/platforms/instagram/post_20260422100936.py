import os
import time
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
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

DEFAULT_INSTAGRAM_IMAGE = r"D:\blockchain_internshipe\Autosocial_ai\default_images\instagram_default.jpg"


def post_to_instagram(driver, post):
    print("Calling Instagram automation...")
    try:
        caption = str(post.caption).strip()

        image_path = ""
        if hasattr(post, "image_path") and post.image_path:
            image_path = str(post.image_path).strip()

        if not image_path:
            image_path = DEFAULT_INSTAGRAM_IMAGE
            print("⚠️ No image found. Using default Instagram image.")

        if not os.path.exists(image_path):
            return {"success": False, "message": f"Image file not found: {image_path}"}

        print("Opening Instagram login...")
        driver.get("https://www.instagram.com/accounts/login/")

        if not wait_for_instagram_login(driver, timeout=180):
            return {"success": False, "message": "Login not completed"}

        print("Opening Instagram home...")
        driver.get("https://www.instagram.com/")
        time.sleep(6)

        print("Finding Create button...")
        create_btn = find_create_button(driver)
        if not create_btn:
            return {"success": False, "message": "Create button not found"}

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
            return {"success": False, "message": "Create button click failed"}

        print("✅ Create button clicked")
        time.sleep(2)

        print("Finding New Post button...")
        new_post_btn = find_new_post_button(driver)
        if new_post_btn:
            safe_click(driver, new_post_btn)
            print("✅ New Post button clicked")
            time.sleep(2)

        print("Looking for 'Select from computer' button...")
        select_btn = find_select_from_computer_button(driver)
        if select_btn:
            safe_click(driver, select_btn)
            print("✅ Clicked 'Select from computer'")
            time.sleep(2)

        print("Finding file input...")
        file_input = find_file_input(driver, timeout=12)
        if not file_input:
            return {"success": False, "message": "Instagram file input not found"}

        file_input.send_keys(image_path)
        print("✅ Image uploaded")
        time.sleep(6)

        print("Clicking first Next...")
        if not click_next(driver):
            return {"success": False, "message": "First Next button not found or not working"}

        print("Clicking second Next...")
        if not click_next(driver):
            return {"success": False, "message": "Second Next button not found or not working"}

        print("Waiting for caption screen...")
        if not wait_for_caption_screen(driver, timeout=15):
            return {"success": False, "message": "Caption/share screen did not open"}

        print("Finding caption box...")
        caption_box = find_caption_box(driver)
        if not caption_box:
            return {"success": False, "message": "Caption box not found"}

        caption_box.click()
        time.sleep(1)

        typed = False

        try:
            type_like_human(caption_box, caption)
            typed = True
            print("✅ Caption entered using type_like_human")
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
                """, caption_box, caption)
                typed = True
                print("✅ Caption entered using JS fallback")
            except Exception as e:
                print("⚠️ JS caption fallback failed:", str(e))

        if not typed:
            return {"success": False, "message": "Caption typing failed"}

        print("Finding Share button...")
share_btn = find_share_button(driver)
if not share_btn:
    return {"success": False, "message": "Share button not found"}

safe_click(driver, share_btn)
print("✅ Share clicked")
time.sleep(8)

    except Exception as e:
        print("❌ Instagram automation error:", str(e))
        return {"success": False, "message": str(e)}