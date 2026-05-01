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
    find_file_input,
    click_next,
    find_caption_box,
    find_share_button,
    wait_for_caption_screen,
)


def post_to_instagram(driver, post):
    """
    Publish a post on Instagram using Selenium automation.

    Flow:
    1. Get caption and media from post object
    2. Open Instagram login page
    3. Wait for user login
    4. Open Instagram home
    5. Click Create / New Post
    6. Upload media directly using file input
    7. Click Next twice
    8. Enter caption
    9. Click Share
    """

    try:
        caption = str(post.caption).strip()
        image_path = ""
        media = None

        if hasattr(post, "media") and post.media:
            try:
                media = post.media

                if isinstance(media, list):
                    image_path = media[0] if media else ""

                elif isinstance(media, str):
                    image_path = media.strip()

                else:
                    image_path = ""

            except Exception:
                image_path = ""

        if not image_path or not os.path.exists(image_path):
            return {
                "success": False,
                "message": f"Image file not found: {image_path}",
            }

        driver.get("https://www.instagram.com/accounts/login/")
        medium_pause()

        if not wait_for_instagram_login(driver, timeout=180):
            screenshot = save_screenshot(driver, prefix="insta_login_failed")
            return {
                "success": False,
                "message": f"Login not completed | {screenshot}",
            }

        driver.get("https://www.instagram.com/")
        log("📸 Instagram opened")
        medium_pause()

        log("➕ Clicking Create button...")
        create_btn = find_create_button(driver)

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

        small_pause()

        new_post_btn = find_new_post_button(driver)

        if new_post_btn:
            safe_click(driver, new_post_btn)
            small_pause()

        file_input = find_file_input(driver, timeout=12)

        if not file_input:
            return {
                "success": False,
                "message": "Instagram file input not found",
            }

        media_files = media if isinstance(media, list) else [media]

        log("🖼 Uploading image...")
        file_input.send_keys("\n".join(media_files))
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

        log("✍️ Adding caption...")

        try:
            type_like_human(caption_box, caption)
            typed = True
        except Exception:
            pass

        if not typed:
            try:
                caption_box.send_keys(caption)
                typed = True
            except Exception:
                pass

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

            except Exception:
                pass

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

        medium_pause()

        return {
            "success": True,
            "message": "Instagram post successful",
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }