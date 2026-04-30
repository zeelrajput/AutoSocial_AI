# automation_engine/platforms/x/post.py

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause

from .utill import (
    open_x_home,
    click_compose_if_needed,
    find_x_textbox,
    type_x_caption,
    find_x_post_button,
    upload_x_image,
)


def post_to_x(driver, post):
    try:
        open_x_home(driver)

        # Optional compose click
        click_compose_if_needed(driver)

        textbox = find_x_textbox(driver, timeout=10)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="x_textbox_not_found")
            return {
                "success": False,
                "message": f"Tweet textbox not found. Screenshot: {screenshot}"
            }

        if not type_x_caption(driver, textbox, post.caption):
            screenshot = save_screenshot(driver, prefix="x_caption_typing_failed")
            return {
                "success": False,
                "message": f"Caption typing failed. Screenshot: {screenshot}"
            }

        if not upload_x_image(driver, post, timeout=10):
            screenshot = save_screenshot(driver, prefix="x_image_upload_failed")
            return {
                "success": False,
                "message": f"Image upload failed. Screenshot: {screenshot}"
            }

        post_button = find_x_post_button(driver, timeout=10)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="x_post_button_not_found")
            return {
                "success": False,
                "message": f"Post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, post_button)
        if not clicked:
            screenshot = save_screenshot(driver, prefix="x_post_button_click_failed")
            return {
                "success": False,
                "message": f"Post button click failed. Screenshot: {screenshot}"
            }

        print("✅ Post button clicked")
        medium_pause()

        return {"success": True, "message": "Post published on X"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="x_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }