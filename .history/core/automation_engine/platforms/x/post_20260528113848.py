import time

from core.automation_engine.common.screenshot_helper import save_screenshot
from core.automation_engine.common.human_behavior import medium_pause
from core.automation_engine.common.logger import clean_log as log

from .utils import (
    open_x_home,
    click_compose_if_needed,
    find_x_textbox,
    type_x_caption,
    upload_x_image,
    find_x_post_button,
    click_x_post_button,
)

def normalize_x_post_url(url):
    if not url:
        return None

    url = url.split("?")[0]

    if "/status/" not in url:
        return None

    return url


def get_latest_x_post_url(driver, timeout=60):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            driver.get("https://x.com/home")
            time.sleep(5)

            post_url = driver.execute_script(
                """
                const links = Array.from(document.querySelectorAll("a[href]"))
                    .map(a => a.href)
                    .filter(h =>
                        h.includes('/status/') &&
                        !h.includes('/analytics') &&
                        !h.includes('/photo/') &&
                        !h.includes('/video/')
                    );

                return links.length ? links[0].split('?')[0] : null;
                """
            )

            normalized = normalize_x_post_url(post_url)

            if normalized:
                return normalized

        except Exception:
            pass

        time.sleep(5)

    return None

def post_to_x(driver, post):
    try:
        log("🐦 Opening X/Twitter...")
        open_x_home(driver)

        log("➕ Opening compose box...")
        click_compose_if_needed(driver)

        textbox = find_x_textbox(driver, timeout=20)

        if not textbox:
            time.sleep(3)
            textbox = find_x_textbox(driver, timeout=10)

        if not textbox:
            screenshot = save_screenshot(driver, platform="x", prefix="x_textbox_not_found")
            return {
                "success": False,
                "message": f"X textbox not found | {screenshot}",
            }

        log("✍️ Adding caption...")
        if not type_x_caption(driver, textbox, post.caption):
            screenshot = save_screenshot(driver,platform="x", prefix="x_typing_failed")
            return {
                "success": False,
                "message": f"X caption typing failed | {screenshot}",
            }

        log("🖼 Uploading image...")
        if not upload_x_image(driver, post):
            screenshot = save_screenshot(driver, platform="x", prefix="x_image_failed")
            return {
                "success": False,
                "message": f"X image upload failed | {screenshot}",
            }

        log("📤 Sharing post...")
        post_btn = find_x_post_button(driver, timeout=20)

        if not post_btn:
            screenshot = save_screenshot(driver, platform="x", prefix="x_post_btn_not_found")
            return {
                "success": False,
                "message": f"X post button not found | {screenshot}",
            }

        if not click_x_post_button(driver, post_btn):
            screenshot = save_screenshot(driver,platform="x", prefix="x_post_click_failed")
            return {
                "success": False,
                "message": f"X post click failed | {screenshot}",
            }

        medium_pause()

        log("🔗 Getting X post URL...")
        post_url = get_latest_x_post_url(driver, timeout=60)
        log(f"🔗 X post URL: {post_url}")

        return {
            "success": True,
            "message": "Post published on X",
            "post_url": post_url,
        }

    except Exception as e:
        screenshot = save_screenshot(driver, platform="x", prefix="x_error")
        return {
            "success": False,
            "message": f"{str(e)} | {screenshot}",
        }
    
    