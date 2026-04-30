import time

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_post_button,
)


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

        clicked = False
        try:
            clicked = safe_click(driver, start_btn)
        except Exception:
            pass

        if not clicked:
            try:
                start_btn.click()
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", start_btn)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "Start post button click failed"}

        print("✅ Start post clicked")
        time.sleep(4)
        close_common_popups(driver)

        print("Finding LinkedIn modal editor...")
        textbox = None

        try:
            textbox = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 40 &&
                        r.height > 20 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                if (!dialogs.length) return null;

                const root = dialogs[dialogs.length - 1];

                const selectors = [
                    "div[contenteditable='true']",
                    "div.ql-editor",
                    "div[role='textbox']",
                    "[contenteditable='true']"
                ];

                for (const sel of selectors) {
                    const nodes = Array.from(root.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;
                        return el;
                    }
                }

                return null;
            """)
        except Exception as e:
            print("⚠️ Modal editor JS failed:", str(e))

        if not textbox:
            try:
                preview = driver.execute_script(
                    "return (document.body.innerText || '').slice(0, 2000);"
                )
                print("🧾 LinkedIn page preview at editor step:", preview)
            except Exception:
                pass
            return {"success": False, "message": "LinkedIn textbox not found"}

        try:
            print("Textbox HTML:", textbox.get_attribute("outerHTML")[:500])
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].focus();", textbox)
            time.sleep(1)
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].click();", textbox)
            time.sleep(1)
        except Exception:
            pass

        typed = False

        try:
            type_like_human(textbox, caption)
            typed = True
            print("✅ Caption entered using type_like_human")
        except Exception as e:
            print("⚠️ type_like_human failed:", str(e))

        if not typed:
            try:
                textbox.send_keys(caption)
                typed = True
                print("✅ Caption entered using send_keys")
            except Exception as e:
                print("⚠️ send_keys failed:", str(e))

        if not typed:
            try:
                driver.execute_script("""
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
                """, textbox, caption)
                typed = True
                print("✅ Caption entered using JS fallback")
            except Exception as e:
                print("⚠️ JS caption fallback failed:", str(e))

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];

                    el.focus();
                    el.textContent = "";
                    el.innerHTML = "";
                    el.textContent = text;

                    el.dispatchEvent(new InputEvent('input', {
                        bubbles: true,
                        cancelable: true,
                        inputType: 'insertText',
                        data: text
                    }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new KeyboardEvent('keyup', {
                        bubbles: true,
                        key: ' '
                    }));
                """, textbox, caption)
                typed = True
                print("✅ Caption entered using strong JS fallback")
            except Exception as e:
                print("⚠️ Strong JS fallback failed:", str(e))

        if not typed:
            return {"success": False, "message": "LinkedIn caption typing failed"}

        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15)
        if not post_btn:
            return {"success": False, "message": "LinkedIn post button not found"}

        clicked = False
        try:
            clicked = safe_click(driver, post_btn)
        except Exception:
            pass

        if not clicked:
            try:
                post_btn.click()
                clicked = True
            except Exception:
                pass

        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", post_btn)
                clicked = True
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "LinkedIn post button click failed"}

        print("✅ LinkedIn post clicked")
        time.sleep(8)

        return {"success": True, "message": "LinkedIn post successful"}

    except Exception as e:
        print("❌ LinkedIn automation error:", str(e))
        return {"success": False, "message": str(e)}