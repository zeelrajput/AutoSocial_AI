import os
import io
import time

from PIL import Image
import win32clipboard

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_image_input,
    find_photo_button,
)


def click_element_robustly(driver, element, name="Element"):
    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, element)),
        ("js_click", lambda: driver.execute_script("arguments[0].click();", element)),
        ("normal_click", lambda: element.click()),
    ]:
        try:
            result = action()
            if result is None or result is True:
                print(f"✅ {name} clicked using {action_name}")
                return True
        except Exception as e:
            print(f"⚠️ {name} {action_name} failed: {e}")
    return False


def type_caption(driver, textbox, caption):
    try:
        driver.execute_script("""
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
        """, textbox)
        time.sleep(1)
    except Exception:
        pass

    try:
        type_like_human(textbox, caption)
        print("✅ Caption entered using type_like_human")
        return True
    except Exception as e:
        print(f"⚠️ type_like_human failed: {e}")

    try:
        textbox.send_keys(caption)
        print("✅ Caption entered using send_keys")
        return True
    except Exception as e:
        print(f"⚠️ send_keys failed: {e}")

    try:
        driver.execute_script("""
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
        """, textbox, caption)
        print("✅ Caption entered using JS fallback")
        return True
    except Exception as e:
        print(f"⚠️ JS caption fallback failed: {e}")

    return False


def copy_image_to_clipboard(media_files):
    image = Image.open(media_files)
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


def paste_image_from_clipboard(driver, textbox, media_files):
    try:
        copy_image_to_clipboard(media_files)
        print("✅ Image copied to clipboard")

        driver.execute_script("""
            arguments[0].scrollIntoView({block:'center'});
            arguments[0].focus();
            arguments[0].click();
        """, textbox)
        time.sleep(1)

        ActionChains(driver) \
            .move_to_element(textbox) \
            .click(textbox) \
            .key_down(Keys.CONTROL) \
            .send_keys("v") \
            .key_up(Keys.CONTROL) \
            .perform()

        print("✅ Image pasted from clipboard")
        time.sleep(6)
        return True

    except Exception as e:
        print("⚠️ Clipboard paste failed:", str(e))
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


def upload_media_if_present(driver, textbox, post):
    media_files = resolve_media_paths(post)
    print("🧾 resolved media_files:", media_files)

    if not media_files:
        print("⚠️ No media/image found on post object")
        return True

    print(f"📸 Uploading media files: {media_files}")

    file_input = find_image_input(driver, timeout=5)

    if not file_input:
        file_input = find_image_input(driver, timeout=5)
if file_input:
    file_input.send_keys("\n".join(media_files))
    print("✅ Image file paths sent before Photo click")
    time.sleep(5)
    return True
        photo_btn = find_photo_button(driver, timeout=10)
        if photo_btn:
            click_element_robustly(driver, photo_btn, "Photo Button")
            time.sleep(3)
            inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            print("Total file inputs after Photo click:", len(inputs))

            for i, inp in enumerate(inputs):
                print("Input", i)
                print("accept:", inp.get_attribute("accept"))
                print("multiple:", inp.get_attribute("multiple"))
                print("outerHTML:", inp.get_attribute("outerHTML")[:500])

            file_input = find_image_input(driver, timeout=10)

    if file_input:
        try:
            file_input.send_keys("\n".join(media_files))
            print("✅ Image file path sent")
            time.sleep(5)
            return True
        except Exception as e:
            print(f"⚠️ File input upload failed: {e}")
            print("⚠️ Trying clipboard fallback...")

    else:
        print("⚠️ No file input found → trying clipboard fallback")

    if len(media_files) > 1:
        print("❌ Multiple images require file input. Clipboard supports only one image.")
        return False

    return paste_image_from_clipboard(driver, textbox, media_files[0])


def wait_for_any_composer(driver, timeout=12):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            textbox = find_linkedin_textbox(driver, timeout=2)
            if textbox and textbox.is_displayed():
                print("✅ LinkedIn composer detected")
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def open_linkedin_composer(driver, start_btn, timeout=12):
    print("🔄 Opening LinkedIn composer...")

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_btn)
        time.sleep(1)
    except Exception:
        pass

    if click_element_robustly(driver, start_btn, "Start Post"):
        if wait_for_any_composer(driver, timeout=4):
            return True

    try:
        driver.execute_script("arguments[0].click();", start_btn)
        print("✅ Start Post clicked using extra JS click")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Extra JS click failed: {e}")

    if wait_for_any_composer(driver, timeout=4):
        return True

    try:
        inner = start_btn.find_element(By.XPATH, ".//*")
        driver.execute_script("arguments[0].click();", inner)
        print("✅ Inner child clicked for composer open")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Inner child click failed: {e}")

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
            result = driver.execute_script("""
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
            """)

            if result and result.get("success"):
                print("✅ LinkedIn post success verified:", result.get("reason"))
                return True

        except Exception as e:
            print("⚠️ verify_linkedin_post_success JS error:", e)

        time.sleep(1)

    return False


def post_using_ctrl_enter(driver, textbox=None):
    try:
        if textbox is not None:
            try:
                driver.execute_script("""
                    arguments[0].scrollIntoView({block:'center'});
                    arguments[0].focus();
                    arguments[0].click();
                """, textbox)
                time.sleep(1)
            except Exception:
                pass

        print("⌨️ Trying CTRL+ENTER...")
        ActionChains(driver) \
            .key_down(Keys.CONTROL) \
            .send_keys(Keys.ENTER) \
            .key_up(Keys.CONTROL) \
            .perform()

        time.sleep(5)
        print("✅ CTRL+ENTER sent")
        return {"triggered": True, "posted": False}
    except Exception as e:
        print("⚠️ CTRL+ENTER failed:", str(e))
        return {"triggered": False, "posted": False}


def find_inline_or_modal_post_button(driver, textbox):
    try:
        result = driver.execute_script("""
            const textbox = arguments[0];

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

            function isEnabled(el) {
                if (!el) return false;
                return !el.disabled && el.getAttribute('aria-disabled') !== 'true';
            }

            function textOf(el) {
                return (
                    (el.innerText || '') + ' ' +
                    (el.textContent || '') + ' ' +
                    (el.getAttribute('aria-label') || '') + ' ' +
                    (el.getAttribute('title') || '') + ' ' +
                    (el.getAttribute('data-control-name') || '')
                ).replace(/\\s+/g, ' ').trim().toLowerCase();
            }

            function blocked(text) {
                const bad = [
                    'start a post',
                    'create a post',
                    'schedule post',
                    'scheduled post',
                    'view all scheduled posts',
                    'photo',
                    'video',
                    'add media',
                    'next',
                    'back',
                    'close'
                ];
                return bad.some(x => text.includes(x));
            }

            function matchesPost(text) {
                return text === 'post' ||
                       text.startsWith('post ') ||
                       text.endsWith(' post') ||
                       text.includes(' post ');
            }

            if (!textbox) return null;

            let node = textbox;
            for (let depth = 0; depth < 12 && node; depth++) {
                const candidates = Array.from(
                    node.querySelectorAll("button, div[role='button'], [aria-label], [title]")
                );

                for (const el of candidates) {
                    const t = textOf(el);
                    if (!isVisible(el) || !isEnabled(el)) continue;
                    if (blocked(t)) continue;
                    if (matchesPost(t)) return el;
                }
                node = node.parentElement;
            }

            const tr = textbox.getBoundingClientRect();
            const all = Array.from(document.querySelectorAll(
                "button, div[role='button'], [aria-label], [title]"
            )).filter(el => isVisible(el) && isEnabled(el));

            let best = null;
            let bestScore = Infinity;

            for (const el of all) {
                const t = textOf(el);
                if (blocked(t)) continue;
                if (!matchesPost(t)) continue;

                const r = el.getBoundingClientRect();
                const score = Math.abs(r.left - tr.left) + Math.abs(r.top - tr.bottom);
                if (score < bestScore) {
                    best = el;
                    bestScore = score;
                }
            }

            return best;
        """, textbox)
        return result
    except Exception as e:
        print(f"⚠️ find_inline_or_modal_post_button error: {e}")
        return None


def click_final_post_button(driver, textbox=None, retries=8):
    time.sleep(3)
    print("🔄 Trying LinkedIn final Post button...")

    for i in range(retries):
        try:
            if textbox is None:
                textbox = find_linkedin_textbox(driver, timeout=3)

            if textbox is None:
                print(f"⚠️ Retry {i+1}: textbox_missing")
                time.sleep(2)
                continue

            btn = find_inline_or_modal_post_button(driver, textbox)
            if btn:
                if click_element_robustly(driver, btn, "Final Post"):
                    time.sleep(5)
                    return verify_linkedin_post_success(driver, timeout=12)

            print(f"⚠️ Retry {i+1}: submit_not_found")

        except Exception as e:
            print(f"⚠️ Retry {i+1} failed: {e}")
            textbox = None

        time.sleep(2)

    print("⚠️ Final Post button failed, trying CTRL+ENTER fallback...")
    ctrl_result = post_using_ctrl_enter(driver, textbox)

    if not ctrl_result.get("triggered"):
        return False

    return verify_linkedin_post_success(driver, timeout=12)


def debug_submit_candidates(driver, textbox=None):
    try:
        result = driver.execute_script("""
            const textbox = arguments[0];

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

            function getText(el) {
                return (
                    (el.innerText || '') + ' | ' +
                    (el.textContent || '') + ' | ' +
                    (el.getAttribute('aria-label') || '') + ' | ' +
                    (el.getAttribute('title') || '') + ' | ' +
                    (el.getAttribute('data-control-name') || '')
                ).replace(/\\s+/g, ' ').trim();
            }

            const all = Array.from(document.querySelectorAll(
                "button, div[role='button'], [aria-label], [title]"
            )).filter(isVisible);

            if (!textbox) {
                return all.slice(0, 80).map(el => getText(el) + " || " + el.outerHTML.slice(0, 250));
            }

            const tr = textbox.getBoundingClientRect();

            return all
                .map(el => {
                    const r = el.getBoundingClientRect();
                    const score = Math.abs(r.left - tr.left) + Math.abs(r.top - tr.bottom);
                    return {
                        text: getText(el),
                        html: el.outerHTML.slice(0, 250),
                        score: score
                    };
                })
                .sort((a, b) => a.score - b.score)
                .slice(0, 40)
                .map(x => `${x.score} || ${x.text} || ${x.html}`);
        """, textbox)

        print("🧾 Submit candidates near textbox:")
        for item in result:
            print(item)

    except Exception as e:
        print("⚠️ debug_submit_candidates failed:", e)


def post_to_linkedin(driver, post):
    print("🚀 Starting LinkedIn automation...")

    try:
        caption = str(getattr(post, "caption", "")).strip()

        if not caption:
            return {"success": False, "message": "Caption is empty"}

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        if not wait_for_linkedin_login(driver, timeout=180):
            return {"success": False, "message": "Login timeout"}

        close_common_popups(driver)

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        close_common_popups(driver)

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        start_btn = find_start_post_button(driver)
        if not start_btn:
            return {"success": False, "message": "Start Post button not found"}

        if not open_linkedin_composer(driver, start_btn, timeout=12):
            return {"success": False, "message": "LinkedIn composer did not open"}

        textbox = find_linkedin_textbox(driver, timeout=20)
        if not textbox:
            return {"success": False, "message": "Textbox not found"}

        if not type_caption(driver, textbox, caption):
            return {"success": False, "message": "Caption typing failed"}

        if not upload_media_if_present(driver, textbox, post):
            return {"success": False, "message": "LinkedIn image upload failed"}

        time.sleep(8)

        try:
            fresh_textbox = find_linkedin_textbox(driver, timeout=5)
            if fresh_textbox:
                textbox = fresh_textbox
                print("✅ Refreshed textbox after media upload")
        except Exception as e:
            print(f"⚠️ Could not refresh textbox reference: {e}")

        if not is_composer_open(driver, textbox):
            print("⚠️ Composer check says closed, but trying final post anyway...")

        debug_submit_candidates(driver, textbox)

        posted = click_final_post_button(driver, textbox)
        if not posted:
            return {"success": False, "message": "LinkedIn did not confirm the post submission"}

        time.sleep(3)

        if verify_linkedin_post_success(driver, timeout=8):
            return {"success": True, "message": "Post submitted successfully"}

        return {"success": False, "message": "Post trigger happened, but LinkedIn did not confirm success"}

    except Exception as e:
        print(f"❌ Automation Error: {str(e)}")
        return {"success": False, "message": str(e)}