import os
import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.upload_helper import upload_file

from .selectors import (
    COMPOSE_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def resolve_media_path(post):
    media_field = getattr(post, "media", None)
    if not media_field:
        return None
    try:
        return media_field.path
    except Exception:
        return str(media_field)


def open_x_home(driver):
    driver.get("https://x.com/home")
    medium_pause()  


def click_compose_if_needed(driver):
    for selector in COMPOSE_SELECTORS:
        try:
            btn = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5) 
            if btn:
                safe_click(driver, btn)  
                print("✅ Compose button clicked:", selector)
                medium_pause()  
                return True
        except Exception:
            continue
    return False


def find_x_textbox(driver):
    for selector in TEXTBOX_SELECTORS:
        try:
            textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=10)  
            print("✅ Textbox found:", selector)
            return textbox
        except Exception:
            continue
    return None



def type_x_caption(textbox, caption):
    try:
        safe_click(None, textbox)  
        small_pause()  

        type_like_human(textbox, caption)  
        print("✅ Caption typed")

        medium_pause()  # ✅ delay after typing
        return True
    except Exception as e:
        print("⚠️ Typing failed:", e)
        return False


# ✅ IMAGE UPLOAD (USING FILE HELPER)
def upload_x_image(driver, post):
    image_path = resolve_media_path(post)

    if not image_path:
        print("ℹ️ No image provided")
        return True

    abs_path = os.path.abspath(str(image_path))
    print("🧾 Image path:", abs_path)

    if not os.path.exists(abs_path):
        print("⚠️ File not found")
        return False

    # ✅ find hidden file inputs
    inputs = driver.find_elements(By.XPATH, "//input[@type='file']")

    for inp in inputs:
        try:
            # ✅ make hidden input visible
            driver.execute_script("""
                arguments[0].style.display='block';
                arguments[0].style.visibility='visible';
            """, inp)

            upload_file(inp, abs_path)  # ✅ your file helper used here
            print("✅ Image uploaded")

            time.sleep(5)
            return True
        except Exception:
            continue

    print("⚠️ Image input not found")
    return False


# ✅ FIND POST BUTTON
def find_x_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            btn = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=10)  # ✅ wait helper
            print("✅ Post button found:", selector)
            return btn
        except Exception:
            continue
    return None