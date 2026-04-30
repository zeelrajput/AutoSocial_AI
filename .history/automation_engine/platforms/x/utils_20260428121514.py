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

        medium_pause() 
        return True
    except Exception as e:
        print("⚠️ Typing failed:", e)
        return False



def upload_x_image(driver, post):
    import os
    from selenium.webdriver.common.by import By

    media_files = getattr(post, "media", None)

    if not media_files:
        print("⚠️ No media found, skipping image upload")
        return True

    if isinstance(media_files, str):
        media_files = [media_files]

    valid_files = []

    for path in media_files:
        if path and os.path.exists(path):
            valid_files.append(path)
        else:
            print("⚠️ File not found:", path)

    if not valid_files:
        return False

    print("🧾 Image paths:", valid_files)

    try:
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys("\n".join(valid_files))
        print("✅ Images uploaded")
        return True

    except Exception as e:
        print("❌ X image upload error:", str(e))
        return False


def find_x_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            btn = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=10)  # ✅ wait helper
            print("✅ Post button found:", selector)
            return btn
        except Exception:
            continue
    return None