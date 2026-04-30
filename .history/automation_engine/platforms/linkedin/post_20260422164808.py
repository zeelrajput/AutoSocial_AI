import time
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_post_button,
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
                        r.width > 10 &&
                        r.height > 10 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const selectors = [
                    "div[role='dialog']",
                    "[aria-label*='Start a post']",
                    "[data-placeholder]",
                    "div[contenteditable='true']",
                    "div[role='textbox']",
                    ".ql-editor"
                ];

                for (const sel of selectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;

                        const text = (
                            (el.innerText || '') + ' ' +
                            (el.textContent || '') + ' ' +
                            (el.getAttribute('aria-label') || '') + ' ' +
                            (el.getAttribute('data-placeholder') || '')
                        ).toLowerCase();

                        if (
                            text.includes('what do you want to talk about') ||
                            text.includes('post to anyone') ||
                            text.includes('rewrite with ai') ||
                            text.includes('create a post') ||
                            text.includes('talk about')
                        ) {
                            return true;
                        }
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

    try:
        inner = start_btn.find_element(By.XPATH, ".//*[@aria-label='Start a post']")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inner)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", inner)
        print("✅ Inner Start a post clicked")
        return True
    except Exception as e:
        print("⚠️ Inner Start post click failed:", str(e))

    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, start_btn)),
        ("normal click", lambda: start_btn.click()),
        ("js click", lambda: driver.execute_script("arguments[0].click();", start_btn)),
    ]:
        try:
            result = action()
            if result is None or result is True:
                print(f"✅ Start post clicked using {action_name}")
                return True
        except Exception as e:
            print(f"⚠️ Start post {action_name} failed:", str(e))

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
        """, textbox)
        time.sleep(1)
    except Exception:
        pass

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
            print("⚠️ Composer open verification failed, but continuing to textbox detection...")
            try:
                preview = driver.execute_script(
                    "return (document.body.innerText || '').slice(0, 3000);"
                )
                print("🧾 LinkedIn page preview after start post click:", preview)
            except Exception:
                pass

        close_common_popups(driver)
        time.sleep(1)

# 🔥 ADD HERE (BEFORE textbox search)
        try:
            iframe_count = driver.execute_script("return document.querySelectorAll('iframe').length;")
            active_html = driver.execute_script("""
                const a = document.activeElement;
                return a ? a.outerHTML || a.tagName : null;
            """)
            print("🧾 iframe count:", iframe_count)
            print("🧾 active element:", active_html)
        except Exception as e:
            print("⚠️ pre-textbox debug failed:", str(e))

        # 👇 EXISTING CODE
        print("Finding LinkedIn textbox...")
        textbox = find_linkedin_textbox(driver, timeout=20)
       
        if not textbox:
                try:
                    debug_html = driver.execute_script("""
                        const nodes = Array.from(document.querySelectorAll("[contenteditable='true'], .ql-editor, div[role='textbox']"));
                        return nodes.slice(0, 15).map((el, i) => {
                            return `#${i}: ` + el.outerHTML.slice(0, 400);
                        }).join("\\n\\n");
                    """)
                    print("🧾 Textbox candidates:", debug_html)
                except Exception as e:
                    print("⚠️ Candidate debug failed:", str(e))

                return {"success": False, "message": "LinkedIn textbox not found"}

        # 🔥 ADD HERE (THIS IS THE CORRECT PLACE)
        if not type_caption(driver, textbox, caption):
            return {"success": False, "message": "Typing failed"}

        time.sleep(2)

        print("Finding Post button...")
        try:
    btn_debug = driver.execute_script("""
        const nodes = Array.from(document.querySelectorAll("button, [role='button'], [aria-label='Post']"));
        return nodes
            .filter(el => {
                const s = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return r.width > 10 && r.height > 10 &&
                       s.display !== 'none' &&
                       s.visibility !== 'hidden' &&
                       s.opacity !== '0';
            })
            .slice(0, 30)
            .map((el, i) => {
                const txt = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).trim();
                return `#${i}: ` + txt + " || " + el.outerHTML.slice(0, 250);
            })
            .join("\\n\\n");
    """)
    print("🧾 Visible button candidates:", btn_debug)
except Exception as e:
    print("⚠️ Post button debug failed:", str(e))
        post_btn = find_post_button(driver, timeout=15)

        if not post_btn:
            return {"success": False, "message": "LinkedIn post button not found"}

        if not type_caption(driver, textbox, caption):
            return {"success": False, "message": "LinkedIn caption typing failed"}

        time.sleep(2)

        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15)
        if not post_btn:
            return {"success": False, "message": "LinkedIn post button not found"}

        if not click_post_button(driver, post_btn):
            return {"success": False, "message": "LinkedIn post button click failed"}

        time.sleep(5)
        return {"success": True, "message": "LinkedIn post successful"}

    except Exception as e:
        print("❌ LinkedIn automation error:", str(e))
        return {"success": False, "message": str(e)}