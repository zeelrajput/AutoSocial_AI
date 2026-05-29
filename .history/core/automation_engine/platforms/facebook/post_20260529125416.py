import os
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.automation_engine.common.tab_manager import open_new_tab
from core.automation_engine.common.human_behavior import small_pause, medium_pause
from core.automation_engine.common.screenshot_helper import save_screenshot
from core.automation_engine.common.click_helper import safe_click
from core.automation_engine.common.type_helper import type_like_human
from core.automation_engine.common.logger import clean_log as log

from .utils import (
    wait_for_facebook_login,
    close_common_popups,
    handle_facebook_security,
    find_create_post_button,
    find_textbox,
    find_photo_video_button,
    find_file_input,
    find_post_button,
    wait_for_uploaded_image_ready,
)


def normalize_text(value):
    return " ".join(str(value or "").split()).lower()


def clean_facebook_url(url):
    if not url:
        return None

    url = url.strip()

    blocked_parts = [
        "comment_id=",
        "/reel/",
        "/watch/",
        "/videos/",
        "/photo.php",
    ]

    if any(part in url for part in blocked_parts):
        return None

    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    remove_keys = [
        "__cft__",
        "__tn__",
        "mibextid",
        "paipv",
        "eav",
        "ref",
        "refid",
        "locale",
    ]

    for key in remove_keys:
        query.pop(key, None)

    clean_query = urlencode(query, doseq=True)

    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        clean_query,
        "",
    ))


def is_facebook_post_url(url):
    if not url:
        return False

    post_markers = [
        "/posts/",
        "story_fbid=",
        "permalink.php",
    ]

    return any(marker in url for marker in post_markers)


def extract_post_urls_from_article(article):
    urls = []

    try:
        links = article.find_elements(
            By.XPATH,
            ".//a[contains(@href,'/posts/') "
            "or contains(@href,'story_fbid=') "
            "or contains(@href,'permalink.php')]"
        )

        for link in links:
            href = link.get_attribute("href")
            clean_url = clean_facebook_url(href)

            if clean_url and is_facebook_post_url(clean_url):
                urls.append(clean_url)

    except Exception:
        pass

    return urls


def collect_visible_post_urls(driver):
    urls = set()

    try:
        articles = driver.find_elements(By.XPATH, "//div[@role='article']")

        for article in articles:
            for url in extract_post_urls_from_article(article):
                urls.add(url)

    except Exception:
        pass

    return urls


def wait_for_dialog_to_close(driver, timeout=30):
    end = time.time() + timeout

    while time.time() < end:
        try:
            dialogs = driver.find_elements(By.XPATH, "//div[@role='dialog']")
            visible_dialogs = [dialog for dialog in dialogs if dialog.is_displayed()]

            if not visible_dialogs:
                return True
        except Exception:
            return True

        time.sleep(1)

    return False


def find_new_facebook_post_url_on_current_page(
    driver,
    caption="",
    existing_urls=None,
    timeout=60,
):
    existing_urls = existing_urls or set()
    caption_needle = normalize_text(caption)[:25]

    end = time.time() + timeout

    while time.time() < end:
        try:
            articles = driver.find_elements(By.XPATH, "//div[@role='article']")

            for article in articles:
                try:
                    if not article.is_displayed():
                        continue

                    article_text = normalize_text(article.text)

                    if caption_needle and caption_needle not in article_text:
                        continue

                    urls = extract_post_urls_from_article(article)

                    for url in urls:
                        if url not in existing_urls:
                            return url

                    if caption_needle and urls:
                        return urls[0]

                except Exception:
                    continue

        except Exception:
            pass

        time.sleep(2)

    return None


def click_with_fallback(driver, element):
    try:
        if safe_click(driver, element):
            return True
    except Exception:
        pass

    try:
        element.click()
        return True
    except Exception:
        pass

    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception:
        pass

    return False


def post_to_facebook(driver, post):
    try:
        caption = str(post.caption or "").strip()
        media_files = []

        if hasattr(post, "media") and post.media:
            media = post.media

            if isinstance(media, list):
                media_files = media
            elif isinstance(media, str):
                media_files = [media]
            elif hasattr(media, "path"):
                media_files = [media.path]

            media_files = [
                str(path).strip()
                for path in media_files
                if path and os.path.exists(str(path).strip())
            ]

        log("📘 Opening Facebook...")
        open_new_tab(driver, "https://www.facebook.com/")
        medium_pause()

        if not wait_for_facebook_login(driver, timeout=20):
            screenshot = save_screenshot(driver, platform="facebook", prefix="fb_login_failed")
            return {
                "success": False,
                "message": f"Facebook login not completed | {screenshot}",
                "post_url": None,
            }

        handle_facebook_security(driver)
        close_common_popups(driver)

        existing_post_urls = collect_visible_post_urls(driver)

        log("➕ Clicking Create Post button...")
        create_btn = find_create_post_button(driver, timeout=15)

        if not create_btn:
            return {
                "success": False,
                "message": "Create post button not found",
                "post_url": None,
            }

        if not click_with_fallback(driver, create_btn):
            return {
                "success": False,
                "message": "Create post button click failed",
                "post_url": None,
            }

        medium_pause()
        close_common_popups(driver)

        if media_files:
            photo_btn = find_photo_video_button(driver, timeout=10)

            if not photo_btn:
                return {
                    "success": False,
                    "message": "Facebook Photo/Video button not found",
                    "post_url": None,
                }

            if not click_with_fallback(driver, photo_btn):
                return {
                    "success": False,
                    "message": "Facebook Photo/Video click failed",
                    "post_url": None,
                }

            medium_pause()

            file_input = find_file_input(driver, timeout=12)

            if not file_input:
                screenshot = save_screenshot(driver, platform="facebook", prefix="fb_image_input_not_found")
                return {
                    "success": False,
                    "message": f"Image input not found | {screenshot}",
                    "post_url": None,
                }

            log("🖼 Uploading image...")
            file_input.send_keys("\n".join(media_files))

            if not wait_for_uploaded_image_ready(driver, timeout=25):
                return {
                    "success": False,
                    "message": "Facebook image preview/upload not ready",
                    "post_url": None,
                }

            time.sleep(2)

        time.sleep(2)
        close_common_popups(driver)

        textbox = find_textbox(driver, timeout=15)

        if not textbox:
            return {
                "success": False,
                "message": "Facebook textbox not found",
                "post_url": None,
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                textbox,
            )
        except Exception:
            pass

        try:
            textbox.click()
            small_pause()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", textbox)
                time.sleep(1)
            except Exception:
                pass

        typed = False

        try:
            log("✍️ Adding caption...")
            type_like_human(textbox, caption)
            typed = True
        except Exception:
            pass

        if not typed:
            try:
                textbox.send_keys(caption)
                typed = True
            except Exception:
                pass

        if not typed:
            try:
                driver.execute_script(
                    """
                    const el = arguments[0];
                    const text = arguments[1];

                    el.focus();

                    if (el.tagName === 'TEXTAREA' || 'value' in el) {
                        el.value = text;
                    } else {
                        el.textContent = text;
                        el.innerHTML = text;
                    }

                    el.dispatchEvent(new InputEvent('input', {
                        bubbles: true,
                        cancelable: true,
                        inputType: 'insertText',
                        data: text
                    }));

                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    """,
                    textbox,
                    caption,
                )
                typed = True
            except Exception:
                pass

        if not typed:
            screenshot = save_screenshot(driver, platform="facebook", prefix="fb_caption_failed")
            return {
                "success": False,
                "message": f"Caption typing failed | {screenshot}",
                "post_url": None,
            }

        if media_files:
            try:
                preview_images = driver.find_elements(
                    By.XPATH,
                    "//div[@role='dialog']//img",
                )

                visible_previews = [
                    img for img in preview_images if img.is_displayed()
                ]

                if len(visible_previews) == 0:
                    screenshot = save_screenshot(driver, platform="facebook", prefix="fb_preview_missing")
                    return {
                        "success": False,
                        "message": f"Image preview missing | {screenshot}",
                        "post_url": None,
                    }

            except Exception as e:
                return {
                    "success": False,
                    "message": f"Facebook preview check failed: {str(e)}",
                    "post_url": None,
                }

        log("📤 Sharing post...")
        post_btn = find_post_button(driver, timeout=15)

        if not post_btn:
            return {
                "success": False,
                "message": "Facebook post button not found",
                "post_url": None,
            }

        if not click_with_fallback(driver, post_btn):
            screenshot = save_screenshot(driver, platform="facebook", prefix="fb_post_click_failed")
            return {
                "success": False,
                "message": f"Post click failed | {screenshot}",
                "post_url": None,
            }

        wait_for_dialog_to_close(driver, timeout=35)
        time.sleep(5)

        post_url = find_new_facebook_post_url_on_current_page(
            driver,
            caption=caption,
            existing_urls=existing_post_urls,
            timeout=60,
        )

        if not post_url:
            screenshot = save_screenshot(driver, platform="facebook", prefix="fb_post_url_not_found")
            return {
                "success": False,
                "message": f"Facebook post may be created, but post URL was not found without page reload | {screenshot}",
                "post_url": None,
            }

        try:
            post.post_url = post_url

            if hasattr(post, "save"):
                post.save(update_fields=["post_url"])
        except Exception as e:
            return {
                "success": False,
                "message": f"Facebook post URL found but failed to save: {str(e)}",
                "post_url": post_url,
            }

        return {
            "success": True,
            "message": "Facebook post successful",
            "post_url": post_url,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "post_url": None,
        }