import os

from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.human_behavior import small_pause, medium_pause

from .selectors import (
    COMPOSE_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def resolve_media_path(post):
    """
    Resolve media path from Django FileField or string path.
    """

    media_field = getattr(post, "media", None)

    if not media_field:
        return None

    try:
        return media_field.path
    except Exception:
        return str(media_field)


def open_x_home(driver):
    """
    Open X home page.
    """

    open_new_tab(driver, "https://www.facebook.com/")
    medium_pause()


def click_compose_if_needed(driver):
    """
    Click the compose button if it is visible/clickable.

    Returns:
        True  -> compose button clicked
        False -> compose button not found
    """

    for selector in COMPOSE_SELECTORS:
        try:
            compose_btn = wait_for_clickable(
                driver,
                By.CSS_SELECTOR,
                selector,
                timeout=5,
            )

            if compose_btn:
                safe_click(driver, compose_btn)
                print(f"✅ Compose button clicked: {selector}")
                medium_pause()
                return True

        except Exception:
            continue

    print("⚠️ Compose button not found, continuing...")
    return False


def find_x_textbox(driver):
    """
    Find X post textbox using multiple selectors.
    """

    for selector in TEXTBOX_SELECTORS:
        try:
            textbox = wait_for_visible(
                driver,
                By.CSS_SELECTOR,
                selector,
                timeout=10,
            )

            print(f"✅ Textbox found: {selector}")
            return textbox

        except Exception:
            continue

    print("❌ X textbox not found")
    return None


def type_x_caption(textbox, caption):
    """
    Type caption into X textbox using human-like typing.
    """

    try:
        safe_click(None, textbox)
        small_pause()

        type_like_human(textbox, caption)
        print("✅ Caption typed")

        medium_pause()
        return True

    except Exception as e:
        print(f"⚠️ Typing failed: {e}")
        return False


def upload_x_image(driver, post):
    """
    Upload image files to X if media exists.

    If no media exists, image upload is skipped.
    """

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
            print(f"⚠️ File not found: {path}")

    if not valid_files:
        print("❌ No valid image files found")
        return False

    print(f"🧾 Image paths: {valid_files}")

    try:
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys("\n".join(valid_files))

        print("✅ Images uploaded")
        return True

    except Exception as e:
        print(f"❌ X image upload error: {e}")
        return False


def find_x_post_button(driver):
    """
    Find final X Post button using multiple selectors.
    """

    for selector in POST_BUTTON_SELECTORS:
        try:
            post_btn = wait_for_clickable(
                driver,
                By.CSS_SELECTOR,
                selector,
                timeout=10,
            )

            print(f"✅ Post button found: {selector}")
            return post_btn

        except Exception:
            continue

    print("❌ X post button not found")
    return None