# automation_engine/platforms/x/utility.py

import os
import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.human_behavior import medium_pause
from .selectors import (
    COMPOSE_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
    IMAGE_INPUT_SELECTORS,
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
            compose_btn = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=5)
            if compose_btn:
                safe_click(driver, compose_btn)
                print("✅ Compose button clicked using:", selector)
                medium_pause()
                return True
        except Exception:
            continue
    return False


def find_x_textbox(driver, timeout=10):
    for selector in TEXTBOX_SELECTORS:
        try:
            textbox = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            if textbox:
                print("✅ Textbox found using:", selector)
                return textbox
        except Exception:
            continue
    return None


def type_x_caption(driver, textbox, caption):
    if not textbox:
        return False

    try:
        safe_click(driver, textbox)
        print("✅ Textbox clicked")
        type_like_human(textbox, caption)
        print("✅ Caption typed")
        medium_pause()
        return True
    except Exception as e:
        print("⚠️ Caption typing failed:", e)
        return False


def find_x_post_button(driver, timeout=10):
    for selector in POST_BUTTON_SELECTORS:
        try:
            post_button = wait_for_clickable(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            if post_button:
                print("✅ Post button found using:", selector)
                return post_button
        except Exception:
            continue
    return None


def upload_x_image(driver, post, timeout=10):
    image_path = resolve_media_path(post)

    if not image_path:
        print("ℹ️ No image found on post object")
        return True

    abs_path = os.path.abspath(str(image_path))
    print("🧾 Resolved image path:", abs_path)

    if not os.path.exists(abs_path):
        print("⚠️ Image file does not exist:", abs_path)
        return False

    for selector in IMAGE_INPUT_SELECTORS:
        try:
            image_input = wait_for_visible(driver, By.CSS_SELECTOR, selector, timeout=timeout)
            if image_input:
                image_input.send_keys(abs_path)
                print("✅ Image uploaded using:", selector)
                time.sleep(5)
                return True
        except Exception:
            continue

    print("⚠️ Image input not found")
    return False