import time
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_text
from automation_engine.common.upload_helper import upload_file
from .selectors import FILE_INPUT
from .utils import (
    find_create_button,
    click_next,
    find_caption_box,
    find_share_button,
)


def post_to_instagram(driver, post):
    print("Calling Instagram automation...")
    try:
        caption = str(post.caption).strip()
        image_path = str(post.image_path).strip()

        print("Opening Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(5)

        print("Finding Create button...")
        create_btn = find_create_button(driver)
        if not create_btn:
            return {"success": False, "message": "Create button not found"}

        safe_click(driver, create_btn)
        print("✅ Create button clicked")
        time.sleep(2)

        print("Finding file input...")
        file_input = driver.find_element(By.XPATH, FILE_INPUT)
        file_input.send_keys(image_path)
        print("✅ Image uploaded")
        time.sleep(3)

        print("Clicking first Next...")
        if not click_next(driver):
            return {"success": False, "message": "First Next button not found"}

        print("Clicking second Next...")
        if not click_next(driver):
            return {"success": False, "message": "Second Next button not found"}

        print("Finding caption box...")
        caption_box = find_caption_box(driver)
        if not caption_box:
            return {"success": False, "message": "Caption box not found"}

        caption_box.click()
        time.sleep(1)
        caption_box.send_keys(caption)
        print("✅ Caption entered")

        print("Finding Share button...")
        share_btn = find_share_button(driver)
        if not share_btn:
            return {"success": False, "message": "Share button not found"}

        safe_click(driver, share_btn)
        print("✅ Share clicked")
        time.sleep(8)

        return {"success": True, "message": "Instagram post successful"}

    except Exception as e:
        print("❌ Instagram automation error:", str(e))
        return {"success": False, "message": str(e)}