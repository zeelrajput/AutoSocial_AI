import time
from selenium.webdriver.common.by import By

from .selectors import (
    START_POST_XPATHS,
    POST_BUTTON_XPATHS,
    CLOSE_POPUP_XPATHS,
)


def wait_for_linkedin_login(driver, timeout=180):
    print("👉 Waiting for LinkedIn login...")
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            current_url = driver.current_url.lower()
            body_text = driver.execute_script(
                "return (document.body.innerText || '').toLowerCase();"
            )

            print("Current URL:", current_url)

            if (
                "linkedin.com" in current_url
                and "login" not in current_url
                and "checkpoint" not in current_url
            ):
                print("✅ LinkedIn login detected")
                return True

            if (
                "verification" in current_url
                or "security verification" in body_text
                or "two-step verification" in body_text
            ):
                print("⏳ Waiting for verification...")
        except Exception as e:
            print("⚠️ LinkedIn login detection error:", str(e))

        time.sleep(2)

    print("❌ LinkedIn login timeout")
    return False


def close_common_popups(driver, timeout=5):
    end_time = time.time() + timeout

    while time.time() < end_time:
        closed_any = False

        for xpath in CLOSE_POPUP_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed():
                            try:
                                el.click()
                            except Exception:
                                driver.execute_script("arguments[0].click();", el)
                            print(f"✅ Closed popup using XPath: {xpath}")
                            time.sleep(2)
                            closed_any = True
                            break
                    except Exception:
                        continue
            except Exception:
                continue

        if not closed_any:
            break


def _find_displayed(driver, xpaths, label):
    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        print(f"✅ {label} found using XPath: {xpath}")
                        try:
                            print(f"{label} HTML:", el.get_attribute("outerHTML")[:500])
                        except Exception:
                            pass
                        return el
                except Exception:
                    continue
        except Exception:
            continue
    return None


def find_start_post_button(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        el = _find_displayed(driver, START_POST_XPATHS, "Start post button")
        if el:
            return el

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

                    if (text.includes('start a post')) {
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
                print("✅ Start post button found using JS fallback")
                return el
        except Exception as e:
            print("⚠️ Start post JS fallback failed:", str(e))

        time.sleep(1)

    return None


def find_post_button(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        el = _find_displayed(driver, POST_BUTTON_XPATHS, "Post button")
        if el:
            return el

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