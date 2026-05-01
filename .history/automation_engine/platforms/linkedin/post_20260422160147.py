import time

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
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
        for action in [
            lambda: safe_click(driver, start_btn),
            lambda: start_btn.click(),
            lambda: driver.execute_script("arguments[0].click();", start_btn),
        ]:
            try:
                result = action()
                clicked = True if result is None else bool(result)
                if clicked:
                    break
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "Start post button click failed"}

        print("✅ Start post clicked")
        time.sleep(3)
        close_common_popups(driver)

        print("Finding LinkedIn textbox...")
        textbox = find_linkedin_textbox(driver, timeout=20)

        if not textbox:
            try:
                preview = driver.execute_script(
                    "return (document.body.innerText || '').slice(0, 3000);"
                )
                print("🧾 LinkedIn page preview at editor step:", preview)
            except Exception:
                pass
            return {"success": False, "message": "LinkedIn textbox not found"}

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
            driver.execute_script("arguments[0].focus();", textbox)
            driver.execute_script("arguments[0].click();", textbox)
            time.sleep(1)
        except Exception:
            pass

        typed = False

        try:
            textbox.clear()
        except Exception:
            pass

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
                    el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: ' ' }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: ' ' }));
                """, textbox, caption)
                typed = True
                print("✅ Caption entered using JS fallback")
            except Exception as e:
                print("⚠️ JS caption fallback failed:", str(e))

        if not typed:
            return {"success": False, "message": "LinkedIn caption typing failed"}

        time.sleep(2)

        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15)
        if not post_btn:
            return {"success": False, "message": "LinkedIn post button not found"}

        clicked = False
        for action in [
            lambda: safe_click(driver, post_btn),
            lambda: post_btn.click(),
            lambda: driver.execute_script("arguments[0].click();", post_btn),
        ]:
            try:
                result = action()
                clicked = True if result is None else bool(result)
                if clicked:
                    break
            except Exception:
                pass

        if not clicked:
            return {"success": False, "message": "LinkedIn post button click failed"}

        print("✅ LinkedIn post clicked")
        time.sleep(5)

        return {"success": True, "message": "LinkedIn post successful"}

    except Exception as e:
        print("❌ LinkedIn automation error:", str(e))
        return {"success": False, "message": str(e)}