import os
import io
import time

from PIL import Image
import win32clipboard

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from core.automation_engine.common.tab_manager import open_new_tab
from core.automation_engine.common.click_helper import safe_click
from core.automation_engine.common.type_helper import type_like_human
from core.automation_engine.common.logger import clean_log as log, get_platform_logger
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_image_input,
    find_photo_button,
)


def click_element_robustly(driver, element, name="Element"):
    for action in [
        lambda: safe_click(driver, element),
        lambda: ActionChains(driver).move_to_element(element).pause(0.3).click().perform(),
        lambda: element.click(),
        lambda: driver.execute_script("arguments[0].click();", element),
    ]:
        try:
            result = action()
            if result is None or result is True:
                return True
        except Exception:
            pass

    return False


def type_caption(driver, textbox, caption):
    try:
        driver.execute_script(
            """
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
            """,
            textbox,
        )
        time.sleep(1)
    except Exception:
        pass

    try:
        type_like_human(textbox, caption)
        return True
    except Exception:
        pass

    try:
        textbox.send_keys(caption)
        return True
    except Exception:
        pass

    try:
        driver.execute_script(
            """
            const el = arguments[0];
            const text = arguments[1];

            el.focus();
            el.click();

            if (el.isContentEditable) {
                el.innerHTML = '';
                el.textContent = text;
            } else if ('value' in el) {
                el.value = text;
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
        return True
    except Exception:
        pass

    return False


def copy_image_to_clipboard(media_file):
    image = Image.open(media_file)

    if image.mode != "RGB":
        image = image.convert("RGB")

    output = io.BytesIO()
    image.save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()

    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


def paste_image_from_clipboard(driver, textbox, media_file):
    try:
        copy_image_to_clipboard(media_file)

        driver.execute_script(
            """
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
            """,
            textbox,
        )

        time.sleep(1)

        ActionChains(driver) \
            .move_to_element(textbox) \
            .click(textbox) \
            .key_down(Keys.CONTROL) \
            .send_keys("v") \
            .key_up(Keys.CONTROL) \
            .perform()

        time.sleep(6)
        return True

    except Exception:
        return False


def resolve_media_paths(post):
    media_field = getattr(post, "media", None)

    if not media_field:
        return []

    if isinstance(media_field, list):
        media_files = media_field
    elif isinstance(media_field, str):
        media_files = [media_field]
    elif hasattr(media_field, "path"):
        media_files = [media_field.path]
    else:
        media_files = []

    return [
        str(path).strip()
        for path in media_files
        if path and os.path.exists(str(path).strip())
    ]


def upload_files_with_windows_dialog(media_files, timeout=15):
    from pywinauto import Desktop

    file_paths = " ".join([f'"{path}"' for path in media_files])
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            dialog = Desktop(backend="uia").window(
                title_re=".*Open.*|.*Upload.*|.*Choose.*"
            )

            if dialog.exists(timeout=1):
                dialog.set_focus()

                edit = dialog.child_window(control_type="Edit")
                edit.set_edit_text(file_paths)

                open_btn = dialog.child_window(
                    title_re=".*Open.*|.*Upload.*",
                    control_type="Button",
                )
                open_btn.click()

                return True

        except Exception:
            pass

        time.sleep(1)

    return False


def upload_media_if_present(driver, textbox, post):
    media_files = resolve_media_paths(post)

    if not media_files:
        return True

    file_input = find_image_input(driver, timeout=5)

    if not file_input:
        file_input = find_image_input(driver, timeout=5)

        if file_input:
            file_input.send_keys("\n".join(media_files))
            time.sleep(5)
            return True

        photo_btn = find_photo_button(driver, timeout=10)

        if photo_btn:
            try:
                photo_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", photo_btn)

            time.sleep(5)

            if len(media_files) > 1:
                uploaded = upload_files_with_windows_dialog(media_files)

                if uploaded:
                    time.sleep(8)
                    return True

                return False

            file_input = find_image_input(driver, timeout=10)

    if file_input:
        try:
            file_input.send_keys("\n".join(media_files))
            time.sleep(5)
            return True
        except Exception:
            pass

    if len(media_files) > 1:
        return False

    return paste_image_from_clipboard(driver, textbox, media_files[0])


def wait_for_any_composer(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            textbox = find_linkedin_textbox(driver, timeout=2)

            if textbox and textbox.is_displayed():
                return True
        except Exception:
            pass

        time.sleep(1)

    return False


def open_linkedin_composer(driver, start_btn, timeout=12):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            start_btn,
        )
        time.sleep(1)
    except Exception:
        pass

    if click_element_robustly(driver, start_btn, "Start Post"):
        if wait_for_any_composer(driver, timeout=4):
            return True

    try:
        driver.execute_script("arguments[0].click();", start_btn)
        time.sleep(2)
    except Exception:
        pass

    if wait_for_any_composer(driver, timeout=4):
        return True

    try:
        inner = start_btn.find_element(By.XPATH, ".//*")
        driver.execute_script("arguments[0].click();", inner)
        time.sleep(2)
    except Exception:
        pass

    return wait_for_any_composer(driver, timeout=4)


def is_composer_open(driver, textbox=None):
    try:
        if textbox is not None:
            try:
                return textbox.is_displayed()
            except Exception:
                pass

        fresh = find_linkedin_textbox(driver, timeout=3)
        return fresh is not None

    except Exception:
        return False


def verify_linkedin_post_success(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            result = driver.execute_script(
                """
                function isVisible(el) {
                    if (!el) return false;

                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);

                    return (
                        r.width > 5 &&
                        r.height > 5 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const bodyText = (document.body.innerText || '').toLowerCase();

                const successHints = [
                    'post shared',
                    'your post was shared',
                    'post successful',
                    'shared successfully'
                ];

                for (const hint of successHints) {
                    if (bodyText.includes(hint)) {
                        return {success: true, reason: hint};
                    }
                }

                const editors = Array.from(document.querySelectorAll(
                    ".ql-editor[contenteditable='true'], div[role='textbox'][contenteditable='true'], div[contenteditable='true']"
                )).filter(isVisible);

                if (editors.length === 0) {
                    return {success: true, reason: "composer_closed"};
                }

                return {success: false, reason: "no_success_yet"};
                """
            )

            if result and result.get("success"):
                return True

        except Exception:
            pass

        time.sleep(1)

    return False


def post_using_ctrl_enter(driver, textbox=None):
    try:
        if textbox is not None:
            try:
                driver.execute_script(
                    """
                    arguments[0].scrollIntoView({block:'center'});
                    arguments[0].focus();
                    arguments[0].click();
                    """,
                    textbox,
                )
                time.sleep(1)
            except Exception:
                pass

        ActionChains(driver) \
            .key_down(Keys.CONTROL) \
            .send_keys(Keys.ENTER) \
            .key_up(Keys.CONTROL) \
            .perform()

        time.sleep(5)

        return {
            "triggered": True,
            "posted": False,
        }

    except Exception:
        return {
            "triggered": False,
            "posted": False,
        }


def find_inline_or_modal_post_button(driver, textbox):
    try:
        return driver.execute_script(
            """
            const textbox = arguments[0];

            function isVisible(el) {
                if (!el) return false;
                const r = el.getBoundingClientRect();
                const s = window.getComputedStyle(el);
                return r.width > 5 &&
                       r.height > 5 &&
                       s.display !== 'none' &&
                       s.visibility !== 'hidden' &&
                       s.opacity !== '0';
            }

            function clickable(el) {
                return el.closest("button, div[role='button']");
            }

            function isEnabled(el) {
                if (!el) return false;
                return !el.disabled &&
                       el.getAttribute('aria-disabled') !== 'true' &&
                       !el.className.toString().includes('disabled') &&
                       !el.className.toString().includes('artdeco-button--disabled');
            }

            function textOf(el) {
                return (
                    (el.innerText || '') + ' ' +
                    (el.textContent || '') + ' ' +
                    (el.getAttribute('aria-label') || '') + ' ' +
                    (el.getAttribute('title') || '')
                ).replace(/\\s+/g, ' ').trim().toLowerCase();
            }

            function isPostButton(el) {
                const t = textOf(el);
                if (!t) return false;

                if (t.includes('start a post')) return false;
                if (t.includes('schedule')) return false;
                if (t.includes('photo')) return false;
                if (t.includes('video')) return false;
                if (t.includes('next')) return false;
                if (t.includes('back')) return false;
                if (t.includes('close')) return false;

                return t === 'post' || t.startsWith('post ');
            }

            const scope =
                textbox.closest('[role="dialog"]') ||
                textbox.closest('.share-box') ||
                document;

            const raw = Array.from(scope.querySelectorAll(
                "button, div[role='button'], [aria-label], [title]"
            ));

            for (const el of raw) {
                const btn = clickable(el);
                if (!btn) continue;
                if (!isVisible(btn)) continue;
                if (!isEnabled(btn)) continue;
                if (isPostButton(btn)) return btn;
            }

            return null;
            """,
            textbox,
        )
    except Exception:
        return None
    

def click_final_post_button(driver, textbox=None, retries=8):
    time.sleep(8)

    for _ in range(retries):
        try:
            if textbox is None:
                textbox = find_linkedin_textbox(driver, timeout=3)

            if textbox is None:
                time.sleep(2)
                continue

            btn = find_inline_or_modal_post_button(driver, textbox)

            if btn:
                if click_element_robustly(driver, btn, "Final Post"):
                    time.sleep(5)
                    return verify_linkedin_post_success(driver, timeout=12)

        except Exception:
            textbox = None

        time.sleep(2)

    ctrl_result = post_using_ctrl_enter(driver, textbox)

    if not ctrl_result.get("triggered"):
        return False

    return verify_linkedin_post_success(driver, timeout=12)

def get_latest_post_url_after_publish(driver, timeout=60):
    end_time = time.time() + timeout

    activity_pages = [
        "https://www.linkedin.com/in/me/recent-activity/all/",
        "https://www.linkedin.com/in/me/recent-activity/posts/",
    ]

    while time.time() < end_time:
        for page_url in activity_pages:
            try:
                driver.get(page_url)
                time.sleep(6)

                post_url = driver.execute_script(
                    """
                    function normalize(url) {
                        if (!url) return null;

                        const urnMatch = url.match(/urn:li:activity:(\\d+)/);
                        if (urnMatch) {
                            return `https://www.linkedin.com/feed/update/urn:li:activity:${urnMatch[1]}`;
                        }

                        const activityMatch = url.match(/activity[-:](\\d+)/);
                        if (activityMatch) {
                            return `https://www.linkedin.com/feed/update/urn:li:activity:${activityMatch[1]}`;
                        }

                        if (url.includes('/feed/update/')) {
                            return url.split('?')[0].replace(/\\/$/, '');
                        }

                        return null;
                    }

                    const selectors = [
                        "[data-urn*='urn:li:activity']",
                        "[data-id*='urn:li:activity']",
                        "div[data-activity-urn]",
                        "article",
                        ".feed-shared-update-v2"
                    ];

                    for (const selector of selectors) {
                        const items = Array.from(document.querySelectorAll(selector));

                        for (const item of items) {
                            const attrs = [
                                item.getAttribute('data-urn'),
                                item.getAttribute('data-id'),
                                item.getAttribute('data-activity-urn')
                            ];

                            for (const attr of attrs) {
                                const normalized = normalize(attr);
                                if (normalized) return normalized;
                            }

                            const links = Array.from(item.querySelectorAll("a[href]"));

                            for (const link of links) {
                                const normalized = normalize(link.href);
                                if (normalized) return normalized;
                            }
                        }
                    }

                    const allLinks = Array.from(document.querySelectorAll("a[href]"));

                    for (const link of allLinks) {
                        const normalized = normalize(link.href);
                        if (normalized) return normalized;
                    }

                    return null;
                    """
                )

                if post_url:
                    return post_url

            except Exception:
                pass

        time.sleep(5)

    return None

def post_to_linkedin(driver, post):
    error_log = get_platform_logger("linkedin")

    try:
        caption = str(getattr(post, "caption", "")).strip()

        if not caption:
            raise RuntimeError("Caption is empty")

        log("Opening LinkedIn...")
        open_new_tab(driver, "https://www.linkedin.com/feed/")
        time.sleep(5)

        if not wait_for_linkedin_login(driver, timeout=180):
            raise RuntimeError("Login timeout")

        close_common_popups(driver)

        time.sleep(3)
        close_common_popups(driver)

        log("Clicking Start Post button...")
        start_btn = find_start_post_button(driver)

        if not start_btn:
            raise RuntimeError("Start Post button not found")

        if not open_linkedin_composer(driver, start_btn, timeout=12):
            raise RuntimeError("LinkedIn composer did not open")

        textbox = find_linkedin_textbox(driver, timeout=20)

        if not textbox:
            raise RuntimeError("Textbox not found")

        log("Adding caption...")

        if not type_caption(driver, textbox, caption):
            raise RuntimeError("Caption typing failed")

        log("Uploading image...")

        if not upload_media_if_present(driver, textbox, post):
            raise RuntimeError("LinkedIn image upload failed")

        time.sleep(8)

        try:
            fresh_textbox = find_linkedin_textbox(driver, timeout=5)

            if fresh_textbox:
                textbox = fresh_textbox
        except Exception:
            pass

        is_composer_open(driver, textbox)

        log("Sharing post...")
        posted = click_final_post_button(driver, textbox)

        if not posted:
            raise RuntimeError("LinkedIn did not confirm the post submission")

        time.sleep(3)

        if not verify_linkedin_post_success(driver, timeout=8):
            raise RuntimeError("Post trigger happened, but LinkedIn did not confirm success")

        log("Getting LinkedIn post URL...")
        post_url = get_latest_post_url_after_publish(driver, timeout=60)
        log(f"LinkedIn post URL: {post_url}")

        error_log.info("No error generated during LinkedIn post")

        return {
            "success": True,
            "message": "Post submitted successfully",
            "post_url": post_url,
        }

    except Exception as exc:
        error_log.exception("LinkedIn post failed")
        clean_message = _clean_error_message(exc)

        log(f"LinkedIn post failed: {clean_message}")

        return {
            "success": False,
            "message": clean_message,
        }
    

def _clean_error_message(exc: Exception) -> str:
    message = str(exc).strip()

    if message:
        return message.split("Stacktrace:")[0].strip()

    return exc.__class__.__name__