import os
import time

from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_add_media_button,
    find_file_input,
    wait_for_uploaded_image_ready,
    find_post_button,
    wait_for_composer_open,
)


def post_to_linkedin(driver, post):
    print("Calling LinkedIn automation...")
    try:
        caption = str(post.caption or "").strip()

        image_path = ""
        if hasattr(post, "media") and post.media:
            try:
                image_path = post.media.path
            except Exception:
                image_path = ""

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
        time.sleep(2)
        close_common_popups(driver)

        if not wait_for_composer_open(driver, timeout=5):
            print("⚠️ Composer not open yet, retrying Start Post click...")
            try:
                driver.execute_script("arguments[0].click();", start_btn)
                time.sleep(2)
            except Exception:
                pass

            if not wait_for_composer_open(driver, timeout=8):
                print("⚠️ Modal composer still not open, checking for inline composer...")

        # 1. Upload image first if provided
        if image_path and os.path.exists(image_path):
            print("Finding Add Media button...")
            media_btn = find_add_media_button(driver, timeout=10)
            if not media_btn:
                return {"success": False, "message": "LinkedIn Add media button not found"}

            clicked = False
            try:
                clicked = safe_click(driver, media_btn)
            except Exception:
                pass

            if not clicked:
                try:
                    media_btn.click()
                    clicked = True
                except Exception:
                    pass

            if not clicked:
                try:
                    driver.execute_script("arguments[0].click();", media_btn)
                    clicked = True
                except Exception:
                    pass

            if not clicked:
                return {"success": False, "message": "LinkedIn Add media click failed"}

            print("✅ Add media clicked")
            time.sleep(3)

            print("Finding image file input...")
            file_input = find_file_input(driver, timeout=12)
            if not file_input:
                return {"success": False, "message": "LinkedIn image file input not found"}

            print("Using media path:", image_path)
            try:
                print("File input accept:", file_input.get_attribute("accept"))
            except Exception:
                pass

            file_input.send_keys(image_path)
            print("✅ Image uploaded")

            print("Waiting for LinkedIn image to finish processing...")
            if not wait_for_uploaded_image_ready(driver, timeout=25):
                return {"success": False, "message": "LinkedIn image preview/upload not ready"}

            time.sleep(2)

        # 2. Find textbox using direct JS
        time.sleep(2)
        close_common_popups(driver)

        print("Finding textbox using placeholder-based JS...")
        textbox = None

        try:
            textbox = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 50 &&
                        r.height > 20 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                const root = dialogs.length ? dialogs[dialogs.length - 1] : document;

                // 1. exact placeholder text
                const allNodes = Array.from(root.querySelectorAll("*"));
                for (const node of allNodes) {
                    const text = (node.innerText || node.textContent || "").trim().toLowerCase();
                    if (!isVisible(node)) continue;

                    if (text.includes("what do you want to talk about")) {
                        let cur = node;
                        for (let i = 0; i < 6 && cur; i++) {
                            const ce = (cur.getAttribute && cur.getAttribute("contenteditable")) || "";
                            const role = (cur.getAttribute && cur.getAttribute("role")) || "";
                            const cls = (cur.className || "").toString().toLowerCase();

                            if (
                                ce === "true" ||
                                role.toLowerCase() === "textbox" ||
                                cls.includes("ql-editor")
                            ) {
                                return cur;
                            }
                            cur = cur.parentElement;
                        }
                    }
                }

                // 2. direct editable candidates
                const selectors = [
                    "div.ql-editor",
                    "div[contenteditable='true']",
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

                // 3. active element fallback
                const active = document.activeElement;
                if (active && isVisible(active)) {
                    return active;
                }

                return null;
            """)
        except Exception as e:
            print("⚠️ JS textbox detection failed:", str(e))

        if not textbox:
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
            return {"success": False, "message": "LinkedIn caption typing failed"}

        # 3. Validate image preview before post
        if image_path and os.path.exists(image_path):
            try:
                preview_images = driver.find_elements(By.XPATH, "//div[@role='dialog']//img")
                visible_previews = [img for img in preview_images if img.is_displayed()]
                print("Visible preview images before post:", len(visible_previews))

                if len(visible_previews) == 0:
                    return {"success": False, "message": "LinkedIn image preview missing before post"}
            except Exception as e:
                print("⚠️ Preview image debug failed:", str(e))
                return {"success": False, "message": f"LinkedIn preview check failed: {str(e)}"}

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