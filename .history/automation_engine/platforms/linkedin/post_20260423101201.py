import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_post_button,
    upload_linkedin_image,
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

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']")).filter(isVisible);
                if (dialogs.length > 0) return true;

                const editors = Array.from(document.querySelectorAll(
                    ".ql-editor, div[contenteditable='true'], div[role='textbox']"
                )).filter(isVisible);

                for (const el of editors) {
                    const txt = (
                        (el.getAttribute('data-placeholder') || '') + ' ' +
                        (el.getAttribute('aria-label') || '') + ' ' +
                        (el.getAttribute('placeholder') || '')
                    ).toLowerCase();

                    if (
                        txt.includes('talk about') ||
                        txt.includes('text editor') ||
                        txt.includes('create a post') ||
                        txt.includes('write') ||
                        el.isContentEditable
                    ) {
                        return true;
                    }
                }

                return false;
            """)
            if opened:
                return True
        except Exception as e:
            print("⚠️ wait_for_composer_open JS error:", str(e))

        time.sleep(1)

    return False


def click_start_post(driver, start_btn):
    print("Clicking Start post...")

    candidates = []

    try:
        candidates.append(start_btn)
    except Exception:
        pass

    try:
        inner = start_btn.find_element(By.XPATH, ".//*[@aria-label='Start a post']")
        candidates.append(inner)
    except Exception:
        pass

    try:
        deep_inner = start_btn.find_element(By.XPATH, ".//*[contains(normalize-space(),'Start a post')]")
        candidates.append(deep_inner)
    except Exception:
        pass

    unique_candidates = []
    seen = set()

    for el in candidates:
        try:
            key = el.id
        except Exception:
            key = str(el)

        if key not in seen:
            seen.add(key)
            unique_candidates.append(el)

    for idx, el in enumerate(unique_candidates):
        for action_name in ["safe_click", "normal_click", "actionchains", "js_click"]:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(1)

                if action_name == "safe_click":
                    safe_click(driver, el)
                elif action_name == "normal_click":
                    el.click()
                elif action_name == "actionchains":
                    ActionChains(driver).move_to_element(el).pause(0.5).click(el).perform()
                elif action_name == "js_click":
                    driver.execute_script("arguments[0].click();", el)

                print(f"✅ Start post clicked using candidate #{idx} with {action_name}")
                time.sleep(2)

                if wait_for_composer_open(driver, timeout=5):
                    print("✅ Composer opened after start post click")
                    return True

            except Exception as e:
                print(f"⚠️ Start post click failed for candidate #{idx} using {action_name}: {e}")

    return False



def click_post_button(driver, post_btn):
    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, post_btn)),
        ("normal click", lambda: post_btn.click()),
        ("js click", lambda: driver.execute_script("arguments[0].click();", post_btn)),
    ]:
        try:
            result = action()
            if result is None or result is True:
                print(f"✅ LinkedIn post clicked using {action_name}")
                return True
        except Exception as e:
            print(f"⚠️ Post button {action_name} failed:", str(e))

    return False


def type_caption(driver, textbox, caption):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
    except Exception:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            el.focus();
            el.click();
            if (el.isContentEditable) {
                const range = document.createRange();
                range.selectNodeContents(el);
                range.collapse(false);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }
        """, textbox)
        time.sleep(1)
    except Exception:
        pass

    try:
        type_like_human(textbox, caption)
        print("✅ Caption entered using type_like_human")
        return True
    except Exception as e:
        print("⚠️ type_like_human failed:", str(e))

    try:
        textbox.send_keys(caption)
        print("✅ Caption entered using send_keys")
        return True
    except Exception as e:
        print("⚠️ send_keys failed:", str(e))

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
        print("⚠️ JS caption fallback failed:", str(e))

    return False


def post_to_linkedin(driver, post):
    print("Calling LinkedIn automation...")

    try:
        caption = str(post.caption or "").strip()

        media_path = None
        if getattr(post, "media", None):
            try:
                media_path = post.media.path
            except Exception:
                try:
                    media_path = str(post.media)
                except Exception:
                    media_path = None

        print("Opening LinkedIn...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        if not wait_for_linkedin_login(driver, timeout=180):
            return {"success": False, "message": "LinkedIn login not completed"}

        close_common_popups(driver)

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        close_common_popups(driver)

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        print("Finding Start Post button...")
        start_btn = find_start_post_button(driver, timeout=15)
        if not start_btn:
            return {"success": False, "message": "Start post button not found"}

        if not click_start_post(driver, start_btn):
            return {"success": False, "message": "Start post button click failed"}

        composer_open = wait_for_composer_open(driver, timeout=10)

        if composer_open:
    print("✅ Composer opened")
else:
    return {"success": False, "message": "LinkedIn composer did not open"}

        close_common_popups(driver)
        time.sleep(1)

        if media_path:
            print("Media path detected:", media_path)
            upload_result = upload_linkedin_image(driver, media_path, timeout=20)
            print("LinkedIn upload result:", upload_result)

            if not upload_result.get("success"):
                return {"success": False, "message": upload_result.get("message", "LinkedIn image upload failed")}
        else:
            print("⚠️ No LinkedIn media found, continuing with text-only post")

        print("Finding LinkedIn textbox...")
        textbox = find_linkedin_textbox(driver, timeout=20)

        if not textbox:
            return {"success": False, "message": "LinkedIn textbox not found"}

        if caption:
            if not type_caption(driver, textbox, caption):
                return {"success": False, "message": "LinkedIn caption typing failed"}

        time.sleep(2)

        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15, textbox=textbox)

        if not post_btn:
            return {"success": False, "message": "LinkedIn post button not found"}

        if not click_post_button(driver, post_btn):
            return {"success": False, "message": "LinkedIn post button click failed"}

        time.sleep(6)

        try:
            composer_still_open = driver.execute_script("""
                const editors = Array.from(document.querySelectorAll("[contenteditable='true'], .ql-editor, div[role='textbox']"));
                return editors.some(el => {
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    const visible = r.width > 5 && r.height > 5 &&
                                    s.display !== 'none' &&
                                    s.visibility !== 'hidden' &&
                                    s.opacity !== '0';
                    const txt = (
                        (el.getAttribute('data-placeholder') || '') + ' ' +
                        (el.getAttribute('aria-label') || '')
                    ).toLowerCase();
                    return visible && (txt.includes('talk about') || txt.includes('text editor'));
                });
            """)
        except Exception:
            composer_still_open = False

        if composer_still_open:
            return {"success": False, "message": "Post button clicked, but composer is still open"}

        return {"success": True, "message": "LinkedIn image/caption post submitted successfully"}

    except Exception as e:
        print("❌ LinkedIn automation error:", str(e))
        return {"success": False, "message": str(e)}