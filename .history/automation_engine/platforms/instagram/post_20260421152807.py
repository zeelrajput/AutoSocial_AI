import time
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_text
from automation_engine.common.upload_helper import upload_file
from automation_engine.common.wait_helper import wait_for_element

from .selectors import *


def post_to_instagram(driver, post):
    try:
        caption = str(post.caption)
        image_path = post.image_path

        # 🔥 Step 1: Open Instagram
        driver.get("https://www.instagram.com/")
        time.sleep(5)

        # 🔥 Step 2: Click Create (+)
        create_btn = find_create_button(driver)
        if not create_btn:
            return {"success": False, "message": "Create button not found"}

        safe_click(driver, create_btn)
        print("✅ Create button clicked")

        time.sleep(2)

        # 🔥 Step 3: Upload Image
        file_input = driver.find_element(By.XPATH, FILE_INPUT)
        upload_file(file_input, image_path)
        print("✅ Image uploaded")

        time.sleep(3)

        # 🔥 Step 4: Next → Next
        click_next(driver)
        click_next(driver)

        # 🔥 Step 5: Enter Caption
        caption_box = find_caption_box(driver)
        if not caption_box:
            return {"success": False, "message": "Caption box not found"}

        type_text(driver, caption_box, caption)
        print("✅ Caption entered")

        time.sleep(2)

        # 🔥 Step 6: Share
        share_btn = find_share_button(driver)
        if not share_btn:
            return {"success": False, "message": "Share button not found"}

        safe_click(driver, share_btn)
        print("✅ Share clicked")

        time.sleep(8)

        return {"success": True, "message": "Instagram post successful"}

    except Exception as e:
        return {"success": False, "message": str(e)}