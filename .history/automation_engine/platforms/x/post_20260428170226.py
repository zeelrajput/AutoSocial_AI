from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.common.click_helper import safe_click

from .utils import (
    open_x_home,
    click_compose_if_needed,
    find_x_textbox,
    type_x_caption,
    upload_x_image,
    find_x_post_button,
)
from automation_engine.common.logger import clean_log as log

def post_to_x(driver, post):
    """
    Publish a post on X using Selenium automation.

    Flow:
    1. Open X home page
    2. Click compose button if required
    3. Find textbox
    4. Type caption
    5. Upload image if available
    6. Click final Post button
    """

    try:
        
        open_x_home(driver)

        click_compose_if_needed(driver)

        textbox = find_x_textbox(driver)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="x_textbox_not_found")
            return {
                "success": False,
                "message": f"Textbox not found | {screenshot}",
            }

        if not type_x_caption(textbox, post.caption):
            screenshot = save_screenshot(driver, prefix="x_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed | {screenshot}",
            }

        if not upload_x_image(driver, post):
            screenshot = save_screenshot(driver, prefix="x_image_failed")
            return {
                "success": False,
                "message": f"Image upload failed | {screenshot}",
            }

        post_btn = find_x_post_button(driver)
        if not post_btn:
            screenshot = save_screenshot(driver, prefix="x_post_btn_not_found")
            return {
                "success": False,
                "message": f"Post button not found | {screenshot}",
            }

        if not safe_click(driver, post_btn):
            screenshot = save_screenshot(driver, prefix="x_post_click_failed")
            return {
                "success": False,
                "message": f"Post click failed | {screenshot}",
            }

        print("✅ X post submitted successfully")
        medium_pause()

        return {
            "success": True,
            "message": "Post published on X",
        }

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="x_error")
        return {
            "success": False,
            "message": f"{str(e)} | {screenshot}",
        }