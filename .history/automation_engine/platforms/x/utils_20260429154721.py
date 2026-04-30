import os

from selenium.webdriver.common.by import By

from automation_engine.common.tab_manager import open_new_tab
from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.human_behavior import small_pause, medium_pause
from automation_engine.common.logger import clean_log as log

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

    log("🐦 Opening X/Twitter...")
    open_new_tab(driver, "https://x.com/home")
    medium_pause()


def click_compose_if_needed(driver):
    """
    Click the compose button if it is visible/clickable.
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
                log("➕ Opening compose box...")
                medium_pause()
                return True

        except Exception:
            continue

    log("⚠️ Compose button not found, continuing...")
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

            return textbox

        except Exception:
            continue

    log("❌ X textbox not found")
    return None


def type_x_caption(textbox, caption):
    """
    Type caption into X textbox using human-like typing.
    """

    try:
        safe_click(None, textbox)
        small_pause()

        log("✍️ Adding caption...")
        type_like_human(textbox, caption)

        medium_pause()
        return True

    except Exception:
        return False


def upload_x_image(driver, post):
    """
    Upload image files to X if media exists.
    """

    media_files = getattr(post, "media", None)

    if not media_files:
        return True

    if isinstance(media_files, str):
        media_files = [media_files]

    valid_files = []

    for path in media_files:
        if path and os.path.exists(path):
            valid_files.append(path)

    if not valid_files:
        return False

    try:
        log("🖼 Uploading image...")
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys("\n".join(valid_files))

        return True

    except Exception:
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

            return post_btn

        except Exception:
            continue

    log("❌ X post button not found")
    return None