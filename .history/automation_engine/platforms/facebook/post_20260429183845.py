import os
import time
import traceback

from selenium.webdriver.common.by import By

from automation_engine.common.tab_manager import open_new_tab
from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.logger import clean_log as log

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


def _debug_page(driver, prefix="facebook_debug"):
    """
    Save screenshot and print current browser state.
    """
    screenshot = None

    try:
        print("🌐 Current URL:", driver.current_url)
        print("📄 Page Title:", driver.title)
    except Exception as e:
        print("⚠️ Could not read page info:", str(e))

    try:
        screenshot = save_screenshot(driver, prefix=prefix)
        print("📸 Screenshot saved:", screenshot)
    except Exception as e:
        print("⚠️ Screenshot failed:", str(e))

    return screenshot


def _click_element(driver, element, error_name="click_failed"):
    """
    Robust click helper.
    """
    clicked = False

    try:
        clicked = safe_click(driver, element)
    except Exception:
        pass

    if not clicked:
        try:
            element.click()
            clicked = True
        except Exception:
            pass

    if not clicked:
        try:
            driver.execute_script("arguments[0].click();", element)
            clicked = True
        except Exception:
            pass

    if not clicked:
        screenshot = save_screenshot(driver, prefix=error_name)
        return False, screenshot

    return True, None


def _normalize_media_files(post):
    media_files = []

    if hasattr(post, "media") and post.media:
        media = post.media

        if isinstance(media, list):
            media_files = media
        elif isinstance(media, str):
            media_files = [media]
        elif hasattr(media, "path"):
            media_files = [media.path]

    valid_files = []

    for path in media_files:
        if not path:
            continue

        clean_path = str(path).strip()

        if os.path.exists(clean_path):
            valid_files.append(clean_path)
        else:
            print("⚠️ Media file not found:", clean_path)

    return valid_files


def post_to_facebook(driver, post):
    try:
        caption = str(getattr(post, "caption", "") or "").strip()
        media_files = _normalize_media_files(post)

        log("📘 Opening Facebook...")
        open_new_tab(driver, "https://www.facebook.com/")
        time.sleep(6)

        _debug_page(driver, prefix="facebook_open_debug")

        if not wait_for_facebook_login(driver, timeout=25):
            screenshot = save_screenshot(driver, prefix="fb_login_failed")

            try:
                print("❌ Facebook login failed URL:", driver.current_url)
                print("❌ Facebook login failed title:", driver.title)
            except Exception:
                pass

            return {
                "success": False,
                "message": f"Facebook login not completed | {screenshot}",
            }

        log("✅ Facebook login detected")

        handle_facebook_security(driver)
        close_common_popups(driver)
        medium_pause()

        log("➕ Clicking Create Post button...")
        create_btn = find_create_post_button(driver, timeout=20)

        if not create_btn:
            screenshot = save_screenshot(driver, prefix="fb_create_post_not_found")
            _debug_page(driver, prefix="fb_create_post_debug")

            return {
                "success": False,
                "message": f"Create post button not found | {screenshot}",
            }

        clicked, screenshot = _click_element(
            driver,
            create_btn,
            error_name="fb_create_post_click_failed",
        )

        if not clicked:
            return {
                "success": False,
                "message": f"Create post button click failed | {screenshot}",
            }

        log("✅ Create Post clicked")
        time.sleep(4)
        close_common_popups(driver)

        if media_files:
            log("🖼 Media found. Opening Photo/Video upload...")
            photo_btn = find_photo_video_button(driver, timeout=15)

            if not photo_btn:
                screenshot = save_screenshot(driver, prefix="fb_photo_button_not_found")

                return {
                    "success": False,
                    "message": f"Facebook Photo/Video button not found | {screenshot}",
                }

            clicked, screenshot = _click_element(
                driver,
                photo_btn,
                error_name="fb_photo_button_click_failed",
            )

            if not clicked:
                return {
                    "success": False,
                    "message": f"Facebook Photo/Video click failed | {screenshot}",
                }

            time.sleep(3)

            file_input = find_file_input(driver, timeout=15)

            if not file_input:
                screenshot = save_screenshot(driver, prefix="fb_image_input_not_found")

                return {
                    "success": False,
                    "message": f"Image input not found | {screenshot}",
                }

            try:
                print("File input accept:", file_input.get_attribute("accept"))
            except Exception:
                pass

            log("🖼 Uploading image...")
            file_input.send_keys("\n".join(media_files))

            if not wait_for_uploaded_image_ready(driver, timeout=30):
                screenshot = save_screenshot(driver, prefix="fb_upload_not_ready")

                return {
                    "success": False,
                    "message": f"Facebook image preview/upload not ready | {screenshot}",
                }

            log("✅ Image uploaded")
            time.sleep(3)

        close_common_popups(driver)
        time.sleep(2)

        log("🔎 Finding Facebook textbox...")
        textbox = find_textbox(driver, timeout=20)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="fb_textbox_not_found")
            _debug_page(driver, prefix="fb_textbox_debug")

            return {
                "success": False,
                "message": f"Facebook textbox not found | {screenshot}",
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                textbox,
            )
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

        if caption:
            try:
                log("✍️ Adding caption...")
                type_like_human(textbox, caption)
                typed = True
            except Exception as e:
                print("⚠️ type_like_human failed:", str(e))

            if not typed:
                try:
                    textbox.send_keys(caption)
                    typed = True
                except Exception as e:
                    print("⚠️ textbox.send_keys failed:", str(e))

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
                        textbox,
                        caption,
                    )
                    typed = True
                except Exception as e:
                    print("⚠️ JS caption insert failed:", str(e))

            if not typed:
                screenshot = save_screenshot(driver, prefix="fb_caption_failed")

                return {
                    "success": False,
                    "message": f"Caption typing failed | {screenshot}",
                }

            log("✅ Caption added")
        else:
            log("⚠️ Empty caption, skipping typing")

        if media_files:
            try:
                preview_images = driver.find_elements(
                    By.XPATH,
                    "//div[@role='dialog']//img",
                )

                visible_previews = [
                    img for img in preview_images if img.is_displayed()
                ]

                if len(visible_previews) == 0:
                    screenshot = save_screenshot(driver, prefix="fb_preview_missing")

                    return {
                        "success": False,
                        "message": f"Image preview missing | {screenshot}",
                    }

                log("✅ Image preview detected")

            except Exception as e:
                screenshot = save_screenshot(driver, prefix="fb_preview_check_failed")

                return {
                    "success": False,
                    "message": f"Facebook preview check failed: {str(e)} | {screenshot}",
                }

        log("📤 Sharing post...")
        post_btn = find_post_button(driver, timeout=20)

        if not post_btn:
            screenshot = save_screenshot(driver, prefix="fb_post_button_not_found")
            _debug_page(driver, prefix="fb_post_button_debug")

            return {
                "success": False,
                "message": f"Facebook post button not found | {screenshot}",
            }

        clicked, screenshot = _click_element(
            driver,
            post_btn,
            error_name="fb_post_click_failed",
        )

        if not clicked:
            return {
                "success": False,
                "message": f"Post click failed | {screenshot}",
            }

        log("✅ Post button clicked")
        time.sleep(6)

        _debug_page(driver, prefix="fb_after_post_debug")

        return {
            "success": True,
            "message": "Facebook post successful",
        }

    except Exception as e:
        screenshot = None

        try:
            screenshot = save_screenshot(driver, prefix="fb_automation_error")
        except Exception:
            pass

        try:
            print("❌ Facebook error URL:", driver.current_url)
            print("❌ Facebook error title:", driver.title)
        except Exception:
            pass

        print("❌ Facebook automation traceback:")
        print(traceback.format_exc())

        return {
            "success": False,
            "message": f"Facebook automation error: {str(e)} | {screenshot}",
        }