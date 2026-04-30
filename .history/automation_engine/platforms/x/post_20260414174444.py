import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.x.selectors import TEXTBOX_SELECTORS, POST_BUTTON_SELECTORS


def post_to_x(driver, post):
    try:
        driver.get("https://x.com/home")
        medium_pause()

        textbox = None
        for selector in TEXTBOX_SELECTORS:
            try:
                textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=10)
                print("Textbox found using:", selector)
                break
            except Exception:
                continue

        if not textbox:
            screenshot = save_screenshot(driver, prefix="x_textbox_not_found")
            return {"success": False, "message": f"Tweet textbox not found. Screenshot: {screenshot}"}

        safe_click(driver, textbox)
        print("Textbox clicked")

        type_like_human(textbox, post.caption)
        print("Caption typed")

        medium_pause()

        post_button = None
        for selector in POST_BUTTON_SELECTORS:
            try:
                post_button = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=10)
                print("Post button found using:", selector)
                break
            except Exception:
                continue

        if not post_button:
            screenshot = save_screenshot(driver, prefix="x_post_button_not_found")
            return {"success": False, "message": f"Post button not found. Screenshot: {screenshot}"}

        clicked = safe_click(driver, post_button)
        if not clicked:
            screenshot = save_screenshot(driver, prefix="x_post_button_click_failed")
            return {"success": False, "message": f"Post button click failed. Screenshot: {screenshot}"}

        print("Post button clicked")
        medium_pause()

        return {"success": True, "message": "Post published on X"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="x_post_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}