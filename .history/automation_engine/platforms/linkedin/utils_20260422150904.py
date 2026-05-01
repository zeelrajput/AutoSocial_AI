import os
import time

from selenium.webdriver.common.by import By

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

        print("Finding Start Post button...")
        start_btn = find_start_post_button(driver, timeout=15)

        if not start_btn:
            return {"success": False, "message": "Start post button not found"}

        try:
            safe_click(driver, start_btn)
        except Exception:
            driver.execute_script("arguments[0].click();", start_btn)

        print("✅ Start post clicked")
        time.sleep(4)

        # ---------------------------------------
        # 🔥 STEP 1: FORCE CLICK COMPOSE AREA
        # ---------------------------------------
        print("Activating LinkedIn editor...")

        try:
            driver.execute_script("""
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

                function clickAny() {
                    const selectors = [
                        "[aria-label*='Start a post']",
                        "[aria-label*='What do you want to talk about']",
                        "div.ql-editor",
                        "div[contenteditable='true']",
                        "div[role='textbox']"
                    ];

                    for (const sel of selectors) {
                        const nodes = document.querySelectorAll(sel);
                        for (const node of nodes) {
                            if (isVisible(node)) {
                                node.click();
                                return true;
                            }
                        }
                    }

                    return false;
                }

                clickAny();
            """)
        except Exception as e:
            print("⚠️ Editor activation failed:", str(e))

        time.sleep(2)

        # ---------------------------------------
        # 🔥 STEP 2: GET REAL EDITOR
        # ---------------------------------------
        print("Getting LinkedIn editor...")

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

                // First try active element
                const active = document.activeElement;
                if (active && isVisible(active)) {
                    return active;
                }

                // Then try global search
                const selectors = [
                    "div.ql-editor",
                    "div[contenteditable='true']",
                    "div[role='textbox']"
                ];

                for (const sel of selectors) {
                    const nodes = document.querySelectorAll(sel);
                    for (const el of nodes) {
                        if (isVisible(el)) {
                            return el;
                        }
                    }
                }

                return null;
            """)
        except Exception as e:
            print("⚠️ Editor detection failed:", str(e))

        if not textbox:
            return {"success": False, "message": "LinkedIn textbox not found"}

        # ---------------------------------------
        # 🔥 STEP 3: FOCUS + TYPE
        # ---------------------------------------
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", textbox)
            driver.execute_script("arguments[0].focus();", textbox)
            driver.execute_script("arguments[0].click();", textbox)
            time.sleep(1)
        except Exception:
            pass

        typed = False

        try:
            type_like_human(textbox, caption)
            typed = True
            print("✅ Typed using human typing")
        except Exception:
            pass

        if not typed:
            try:
                textbox.send_keys(caption)
                typed = True
                print("✅ Typed using send_keys")
            except Exception:
                pass

        if not typed:
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];

                    el.focus();
                    el.innerHTML = "";
                    el.textContent = text;

                    el.dispatchEvent(new InputEvent('input', {bubbles:true}));
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                """, textbox, caption)
                typed = True
                print("✅ Typed using JS fallback")
            except Exception:
                pass

        if not typed:
            return {"success": False, "message": "Typing failed"}

        time.sleep(2)

        # ---------------------------------------
        # 🔥 STEP 4: POST
        # ---------------------------------------
        print("Finding Post button...")
        post_btn = find_post_button(driver, timeout=15)

        if not post_btn:
            return {"success": False, "message": "Post button not found"}

        try:
            safe_click(driver, post_btn)
        except Exception:
            driver.execute_script("arguments[0].click();", post_btn)

        print("✅ LinkedIn post clicked")
        time.sleep(6)

        return {"success": True, "message": "LinkedIn post successful"}

    except Exception as e:
        print("❌ LinkedIn automation error:", str(e))
        return {"success": False, "message": str(e)}