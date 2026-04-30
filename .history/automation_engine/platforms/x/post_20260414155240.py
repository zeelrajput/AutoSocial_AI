import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.type_helper import type_like_human
from automation_engine.platforms.x.selectors import TEXTBOX_SELECTORS, POST_BUTTON_SELECTORS


def post_to_x(driver, post):
    try:
        driver.get("https://x.com/home")
        time.sleep(5)

        textbox = None
        for selector in TEXTBOX_SELECTORS:
            try:
                textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=10)
                break
            except Exception:
                continue

        if not textbox:
            return {"success": False, "message": "Tweet textbox not found"}

        textbox.click()
        type_like_human(textbox, post.caption)

        time.sleep(2)

        post_button = None
        for selector in POST_BUTTON_SELECTORS:
            try:
                post_button = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=10)
                break
            except Exception:
                continue

        if not post_button:
            return {"success": False, "message": "Post button not found"}

        post_button.click()
        time.sleep(5)

        return {"success": True, "message": "Post published on X"}

    except Exception as e:
        return {"success": False, "message": str(e)}