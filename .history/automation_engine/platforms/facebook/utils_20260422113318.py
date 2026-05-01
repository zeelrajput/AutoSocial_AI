import time
from selenium.webdriver.common.by import By

from .selectors import (
    CREATE_POST_XPATHS,
    TEXTBOX_XPATHS,
    PHOTO_VIDEO_XPATHS,
    FILE_INPUT_XPATHS,
    POST_BUTTON_XPATHS,
)



def wait_for_facebook_login(driver, timeout=180):
    print("👉 Waiting for Facebook login...")
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            current_url = driver.current_url.lower()
            body_text = driver.execute_script(
                "return (document.body.innerText || '').toLowerCase();"
            )

            print("Current URL:", current_url)

            # logged in if on facebook and not on login/checkpoint pages
            if (
                "facebook.com" in current_url
                and "login" not in current_url
                and "checkpoint" not in current_url
            ):
                print("✅ Facebook login detected")
                return True

            if (
                "two-factor" in current_url
                or "checkpoint" in current_url
                or "approve your login" in body_text
                or "enter the code" in body_text
            ):
                print("⏳ Waiting for verification...")
        except Exception as e:
            print("⚠️ Facebook login detection error:", str(e))

        time.sleep(2)

    print("❌ Facebook login timeout")
    return False


def _find_displayed(driver, xpaths, label):
    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print(f"✅ {label} found using XPath: {xpath}")
                        return el
                except Exception:
                    continue
        except Exception:
            continue
    return None


def find_create_post_button(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        # 1. XPath tries
        for xpath in CREATE_POST_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed():
                            print(f"✅ Create post button found using XPath: {xpath}")
                            print("Create Post HTML:", el.get_attribute("outerHTML")[:500])
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # 2. JS fallback
        try:
            el = driver.execute_script("""
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

                function isClickable(el) {
                    if (!el) return false;
                    const tag = (el.tagName || '').toLowerCase();
                    const role = (el.getAttribute('role') || '').toLowerCase();
                    return tag === 'button' || role === 'button';
                }

                const nodes = Array.from(document.querySelectorAll("*"));

                for (const node of nodes) {
                    const text = (node.innerText || node.textContent || '').trim().toLowerCase();
                    if (!isVisible(node)) continue;

                    if (
                        text.includes("what's on your mind") ||
                        text.includes("create post")
                    ) {
                        let cur = node;
                        for (let i = 0; i < 5 && cur; i++) {
                            if (isClickable(cur)) return cur;
                            cur = cur.parentElement;
                        }
                        return node;
                    }
                }
                return null;
            """)
            if el:
                print("✅ Create post button found using JS fallback")
                print("Create Post HTML:", el.get_attribute("outerHTML")[:500])
                return el
        except Exception as e:
            print("⚠️ Create post JS fallback failed:", str(e))

        try:
            preview = driver.execute_script(
                "return (document.body.innerText || '').slice(0, 1500);"
            )
            print("🧾 Facebook page preview:", preview)
        except Exception:
            pass

        time.sleep(1)

    return None


def find_textbox(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        el = _find_displayed(driver, TEXTBOX_XPATHS, "Textbox")
        if el:
            try:
                print("Textbox HTML:", el.get_attribute("outerHTML")[:500])
            except Exception:
                pass
            return el

        try:
            el = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return r.width > 20 && r.height > 20 &&
                           s.display !== 'none' &&
                           s.visibility !== 'hidden' &&
                           s.opacity !== '0';
                }

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                const root = dialogs.length ? dialogs[dialogs.length - 1] : document;
                const nodes = Array.from(root.querySelectorAll("div[role='textbox'], [contenteditable='true']"));

                for (const node of nodes) {
                    if (!isVisible(node)) continue;
                    return node;
                }
                return null;
            """)
            if el:
                print("✅ Textbox found using JS fallback")
                return el
        except Exception as e:
            print("⚠️ Textbox JS fallback failed:", str(e))

        time.sleep(1)

    return None


def find_photo_video_button(driver):
    return _find_displayed(driver, PHOTO_VIDEO_XPATHS, "Photo/Video button")


def find_file_input(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        for xpath in FILE_INPUT_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    return el
            except Exception:
                continue
        time.sleep(1)

    return None


def find_post_button(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        el = _find_displayed(driver, POST_BUTTON_XPATHS, "Post button")
        if el:
            try:
                print("Post button HTML:", el.get_attribute("outerHTML")[:500])
            except Exception:
                pass
            return el

        try:
            el = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return r.width > 20 && r.height > 20 &&
                           s.display !== 'none' &&
                           s.visibility !== 'hidden' &&
                           s.opacity !== '0';
                }

                function isClickable(el) {
                    if (!el) return false;
                    const tag = (el.tagName || '').toLowerCase();
                    const role = (el.getAttribute('role') || '').toLowerCase();
                    return tag === 'button' || role === 'button';
                }

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                const root = dialogs.length ? dialogs[dialogs.length - 1] : document;
                const nodes = Array.from(root.querySelectorAll("*"));

                for (const node of nodes) {
                    const text = (node.innerText || node.textContent || '').trim().toLowerCase();
                    if (!isVisible(node)) continue;

                    if (text === 'post') {
                        let cur = node;
                        for (let i = 0; i < 5 && cur; i++) {
                            if (isClickable(cur)) return cur;
                            cur = cur.parentElement;
                        }
                        return node;
                    }
                }
                return null;
            """)
            if el:
                print("✅ Post button found using JS fallback")
                return el
        except Exception as e:
            print("⚠️ Post button JS fallback failed:", str(e))

        time.sleep(1)

    return None