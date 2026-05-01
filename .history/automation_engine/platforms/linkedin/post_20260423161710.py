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


def wait_for_composer_open(driver, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            opened = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 20 &&
                        r.height > 20 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"))
                    .filter(isVisible);

                if (!dialogs.length) return false;

                const root = dialogs[dialogs.length - 1];
                const txt = (
                    (root.innerText || '') + ' ' +
                    (root.textContent || '')
                ).toLowerCase();

                return (
                    txt.includes('create a post') ||
                    txt.includes('post to anyone') ||
                    txt.includes('what do you want to talk about') ||
                    root.querySelector("[contenteditable='true'], .ql-editor, div[role='textbox'], button") !== null
                );
            """)
            if opened:
                return True
        except Exception as e:
            print(f"⚠️ Composer wait JS error: {e}")

        time.sleep(1)

    return False


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
            continue
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


def copy_image_to_clipboard(image_path):
    image = Image.open(image_path)
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


def paste_image_from_clipboard(driver, textbox, image_path):
    try:
        copy_image_to_clipboard(image_path)
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


def resolve_media_path(post):
    media_field = getattr(post, "media", None)
    if not media_field:
        return None

    try:
        return media_field.path
    except Exception:
        return str(media_field)


def upload_media_if_present(driver, textbox, post):
    image_path = resolve_media_path(post)
    print("🧾 resolved image_path:", image_path)

    if not image_path:
        print("⚠️ No media/image found on post object")
        return True

    abs_path = os.path.abspath(str(image_path))
    print(f"📸 Uploading: {abs_path}")

    if not os.path.exists(abs_path):
        print("⚠️ Image file does not exist on disk")
        return False

    file_input = find_image_input(driver, timeout=5)

    if not file_input:
        photo_btn = find_photo_button(driver, timeout=5)
        if photo_btn:
            click_element_robustly(driver, photo_btn, "Photo Button")
            time.sleep(3)
            file_input = find_image_input(driver, timeout=10)

    if file_input:
        try:
            file_input.send_keys(abs_path)
            print("✅ Image file path sent")
            time.sleep(5)
            return True
        except Exception as e:
            print(f"⚠️ File input upload failed: {e}")
            print("⚠️ Trying clipboard fallback...")

    else:
        print("⚠️ No file input found → trying clipboard fallback")

    return paste_image_from_clipboard(driver, textbox, abs_path)


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

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"))
                    .filter(isVisible);

                if (dialogs.length > 0) {
                    return {success: false, reason: "dialog_still_open"};
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
    

def click_final_post_button(driver, textbox=None, retries=8):
    time.sleep(4)
    print("🔄 Trying LinkedIn final Post button...")

    for i in range(retries):
        try:
            if textbox is None:
                try:
                    textbox = find_linkedin_textbox(driver, timeout=3)
                except Exception:
                    textbox = None

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

                function getText(el) {
                    return (
                        (el.innerText || '') + ' ' +
                        (el.textContent || '') + ' ' +
                        (el.getAttribute('aria-label') || '') + ' ' +
                        (el.getAttribute('data-control-name') || '') + ' ' +
                        (el.getAttribute('title') || '')
                    ).replace(/\\s+/g, ' ').trim().toLowerCase();
                }

                function isRealSubmitButton(el) {
                    if (!isVisible(el) || !isEnabled(el)) return false;

                    const text = getText(el);

                    const blocked = [
                        'start a post',
                        'create a post',
                        'post to anyone',
                        'what do you want to talk about',
                        'add media',
                        'add photo',
                        'schedule post',
                        'scheduled post',
                        'view all scheduled posts',
                        'next',
                        'back',
                        'close'
                    ];

                    for (const bad of blocked) {
                        if (text.includes(bad)) return false;
                    }

                    // Accept only exact real publish button text
                    return (
                        text === 'post' ||
                        text === 'post ' ||
                        text === ' post'
                    );
                }

                function findSubmitInRoot(root) {
                    if (!root) return null;

                    const candidates = Array.from(
                        root.querySelectorAll("button, div[role='button'], [aria-label], [title]")
                    );

                    for (const el of candidates) {
                        if (isRealSubmitButton(el)) return el;
                    }

                    return null;
                }

                // 1. Dialog first
                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"))
                    .filter(isVisible);

                if (dialogs.length) {
                    const btn = findSubmitInRoot(dialogs[dialogs.length - 1]);
                    if (btn) {
                        btn.click();
                        return {
                            clicked: true,
                            mode: "dialog",
                            html: btn.outerHTML.slice(0, 500)
                        };
                    }
                }

                // 2. Use real Selenium textbox
                if (!textbox) {
                    return {clicked: false, reason: "textbox_missing"};
                }

                let node = textbox;
                for (let depth = 0; depth < 15 && node; depth++) {
                    const btn = findSubmitInRoot(node);
                    if (btn) {
                        btn.click();
                        return {
                            clicked: true,
                            mode: "textbox_ancestor",
                            html: btn.outerHTML.slice(0, 500)
                        };
                    }
                    node = node.parentElement;
                }

                // 3. nearest exact POST button only
                const tr = textbox.getBoundingClientRect();
                const allCandidates = Array.from(document.querySelectorAll(
                    "button, div[role='button'], [aria-label], [title]"
                )).filter(el => isVisible(el) && isEnabled(el));

                let best = null;
                let bestScore = Infinity;

                for (const el of allCandidates) {
                    if (!isRealSubmitButton(el)) continue;

                    const r = el.getBoundingClientRect();
                    const dx = Math.abs(r.left - tr.left);
                    const dy = Math.abs(r.top - tr.bottom);
                    const score = dx + dy;

                    if (score < bestScore) {
                        best = el;
                        bestScore = score;
                    }
                }

                if (best) {
                    best.click();
                    return {
                        clicked: true,
                        mode: "nearest_to_textbox",
                        html: best.outerHTML.slice(0, 500)
                    };
                }

                return {clicked: false, reason: "submit_not_found"};
            """, textbox)

            if result and result.get("clicked"):
                print(f"✅ Final Post button clicked on retry {i+1}")
                print("🧾 Mode:", result.get("mode"))
                print("🧾 Clicked button HTML:", result.get("html"))
                time.sleep(5)
                return verify_linkedin_post_success(driver, timeout=12)

            print(f"⚠️ Retry {i+1}: {result.get('reason') if result else 'unknown'}")

            try:
                _ = textbox.tag_name
            except Exception:
                textbox = None

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

        if not click_element_robustly(driver, start_btn, "Start Post"):
            return {"success": False, "message": "Could not click Start Post"}

        if not wait_for_composer_open(driver, timeout=15):
            print("⚠️ Composer open check failed, continuing...")

        textbox = find_linkedin_textbox(driver, timeout=20)
        if not textbox:
            return {"success": False, "message": "Textbox not found"}

        if not type_caption(driver, textbox, caption):
            return {"success": False, "message": "Caption typing failed"}

        if not upload_media_if_present(driver, textbox, post):
            return {"success": False, "message": "LinkedIn image upload failed"}

        time.sleep(3)

        # LinkedIn may rerender editor after media upload
        try:
            fresh_textbox = find_linkedin_textbox(driver, timeout=5)
            if fresh_textbox:
                textbox = fresh_textbox
        except Exception as e:
            print(f"⚠️ Could not refresh textbox reference: {e}")

        if not is_composer_open(driver, textbox):
            print("⚠️ Composer check says closed, but trying final post anyway...")

        debug_submit_candidates(driver, textbox)

        posted = click_final_post_button(driver, textbox)
        if not posted:
            return {"success": False, "message": "LinkedIn did not confirm the post submission"}

        time.sleep(3)

        # Final verification
        if verify_linkedin_post_success(driver, timeout=8):
            return {"success": True, "message": "Post submitted successfully"}

        return {"success": False, "message": "Post trigger happened, but LinkedIn did not confirm success"}

    except Exception as e:
        print(f"❌ Automation Error: {str(e)}")
        return {"success": False, "message": str(e)}