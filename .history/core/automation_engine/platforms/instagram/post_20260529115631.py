import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.automation_engine.common.human_behavior import (
    small_pause,
    medium_pause,
)
from core.automation_engine.common.screenshot_helper import (
    save_screenshot,
)
from core.automation_engine.common.click_helper import (
    safe_click,
)
from core.automation_engine.common.type_helper import (
    type_like_human,
)
from core.automation_engine.common.logger import (
    clean_log as log,
)
from core.automation_engine.common.tab_manager import (
    open_new_tab,
)

from .utils import (
    wait_for_instagram_login,
    find_create_button,
    click_next,
    find_caption_box,
    find_share_button,
    wait_for_caption_screen,
)


def get_latest_instagram_post_url(driver):

    try:

        driver.get("https://www.instagram.com/accounts/edit/")

        time.sleep(5)

        username_input = driver.find_element(
            By.XPATH,
            "//input[@name='username']"
        )

        username = username_input.get_attribute("value")

        if not username:
            return ""

        driver.get(f"https://www.instagram.com/{username}/")

        time.sleep(5)

        latest_post = driver.find_element(
            By.XPATH,
            "(//article//a[contains(@href,'/p/')])[1]"
        )

        return latest_post.get_attribute("href")

    except Exception as e:

        log(f"❌ Post URL fetch failed: {str(e)}")

        return ""


def post_to_instagram(driver, post):

    try:

        # ---------------------------------------------------
        # CAPTION
        # ---------------------------------------------------

        caption = str(post.caption or "").strip()

        # ---------------------------------------------------
        # IMAGE PATH
        # ---------------------------------------------------

        image_path = ""

        media = None

        if hasattr(post, "media") and post.media:

            media = post.media

            if isinstance(media, list):

                image_path = media[0] if media else ""

            elif isinstance(media, str):

                image_path = media.strip()

            elif hasattr(media, "path"):

                image_path = media.path

        if not image_path:

            return {
                "success": False,
                "message": "Instagram image path missing",
            }

        image_path = os.path.abspath(str(image_path))

        if not os.path.exists(image_path):

            return {
                "success": False,
                "message": f"Image not found: {image_path}",
            }

        # ---------------------------------------------------
        # OPEN INSTAGRAM
        # ---------------------------------------------------

        open_new_tab(driver, "https://www.instagram.com/")

        log("📸 Instagram opened")

        medium_pause()

        # ---------------------------------------------------
        # LOGIN CHECK
        # ---------------------------------------------------

        if not wait_for_instagram_login(driver, timeout=180):

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_login_failed"
            )

            return {
                "success": False,
                "message": f"Instagram login failed | {screenshot}",
            }

        # ---------------------------------------------------
        # CLICK CREATE BUTTON
        # ---------------------------------------------------

        log("➕ Clicking Create button...")

        create_btn = find_create_button(driver)

        if not create_btn:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_create_missing"
            )

            return {
                "success": False,
                "message": f"Create button not found | {screenshot}",
            }

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

                driver.execute_script(
                    "arguments[0].click();",
                    create_btn
                )

                clicked = True

            except Exception:
                pass

        if not clicked:

            return {
                "success": False,
                "message": "Create button click failed",
            }

        small_pause()

        # ---------------------------------------------------
        # CLICK POST OPTION
        # ---------------------------------------------------

        log("📝 Clicking Post option...")

        try:

            post_option = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[text()='Post']"
                ))
            )

            driver.execute_script(
                "arguments[0].click();",
                post_option
            )

        except Exception as e:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_post_option_failed"
            )

            return {
                "success": False,
                "message": f"Post option failed: {str(e)} | {screenshot}",
            }

        # IMPORTANT WAIT
        time.sleep(5)

        # ---------------------------------------------------
        # FIND FILE INPUT
        # ---------------------------------------------------

        log("🖼 Finding upload input...")

        file_input = None

        try:

            file_inputs = driver.find_elements(
                By.XPATH,
                "//input[@type='file']"
            )

            for inp in file_inputs:

                try:

                    accept = inp.get_attribute("accept")

                    if accept:

                        file_input = inp
                        break

                except Exception:
                    pass

        except Exception:
            pass

        # JS fallback
        if not file_input:

            try:

                file_input = driver.execute_script("""
                    return document.querySelector('input[type=file]');
                """)

            except Exception:
                pass

        if not file_input:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_file_input_missing"
            )

            return {
                "success": False,
                "message": f"Instagram file input not found | {screenshot}",
            }

        # ---------------------------------------------------
        # MAKE INPUT VISIBLE
        # ---------------------------------------------------

        try:

            driver.execute_script("""
                arguments[0].style.display = 'block';
                arguments[0].style.visibility = 'visible';
                arguments[0].style.opacity = 1;
            """, file_input)

        except Exception:
            pass

        # ---------------------------------------------------
        # UPLOAD IMAGE
        # ---------------------------------------------------

        log(f"📤 Uploading image: {image_path}")

        try:

            file_input.send_keys(image_path)

        except Exception as e:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_upload_failed"
            )

            return {
                "success": False,
                "message": f"Image upload failed: {str(e)} | {screenshot}",
            }

        # IMPORTANT WAIT
        time.sleep(10)

        # ---------------------------------------------------
        # FIRST NEXT
        # ---------------------------------------------------

        log("➡ Clicking first Next...")

        if not click_next(driver):

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_first_next_failed"
            )

            return {
                "success": False,
                "message": f"First Next failed | {screenshot}",
            }

        time.sleep(3)

        # ---------------------------------------------------
        # SECOND NEXT
        # ---------------------------------------------------

        log("➡ Clicking second Next...")

        if not click_next(driver):

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_second_next_failed"
            )

            return {
                "success": False,
                "message": f"Second Next failed | {screenshot}",
            }

        # ---------------------------------------------------
        # WAIT FOR CAPTION SCREEN
        # ---------------------------------------------------

        if not wait_for_caption_screen(driver, timeout=20):

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_caption_screen_failed"
            )

            return {
                "success": False,
                "message": f"Caption screen failed | {screenshot}",
            }

        # ---------------------------------------------------
        # FIND CAPTION BOX
        # ---------------------------------------------------

        caption_box = find_caption_box(driver)

        if not caption_box:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_caption_missing"
            )

            return {
                "success": False,
                "message": f"Caption box missing | {screenshot}",
            }

        try:

            caption_box.click()

            time.sleep(1)

        except Exception:
            pass

        # ---------------------------------------------------
        # TYPE CAPTION
        # ---------------------------------------------------

        typed = False

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

                    if ('value' in el) {
                        el.value = text;
                    } else {
                        el.textContent = text;
                    }

                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    """,
                    caption_box,
                    caption
                )

                typed = True

            except Exception:
                pass

        if not typed:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_caption_failed"
            )

            return {
                "success": False,
                "message": f"Caption typing failed | {screenshot}",
            }

        # ---------------------------------------------------
        # FIND SHARE BUTTON
        # ---------------------------------------------------

        log("📤 Clicking Share button...")

        share_btn = find_share_button(driver)

        if not share_btn:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_share_missing"
            )

            return {
                "success": False,
                "message": f"Share button missing | {screenshot}",
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

                driver.execute_script(
                    "arguments[0].click();",
                    share_btn
                )

                clicked = True

            except Exception:
                pass

        if not clicked:

            screenshot = save_screenshot(
                driver,
                platform="instagram",
                prefix="insta_share_failed"
            )

            return {
                "success": False,
                "message": f"Share click failed | {screenshot}",
            }

        # ---------------------------------------------------
        # WAIT FOR POSTING
        # ---------------------------------------------------

        log("⏳ Waiting for upload completion...")

        time.sleep(15)

        # ---------------------------------------------------
        # FETCH POST URL
        # ---------------------------------------------------

        post_url = get_latest_instagram_post_url(driver)

        # ---------------------------------------------------
        # SAVE URL
        # ---------------------------------------------------

        try:

            if post_url and hasattr(post, "post_url"):

                post.post_url = post_url

                if hasattr(post, "save"):

                    post.save(update_fields=["post_url"])

        except Exception:
            pass

        # ---------------------------------------------------
        # SUCCESS
        # ---------------------------------------------------

        return {
            "success": True,
            "message": "Instagram post successful",
            "post_url": post_url,
        }

    except Exception as e:

        screenshot = save_screenshot(
            driver,
            platform="instagram",
            prefix="insta_unknown_error"
        )

        return {
            "success": False,
            "message": f"{str(e)} | {screenshot}",
        }