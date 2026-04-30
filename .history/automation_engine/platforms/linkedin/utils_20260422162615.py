import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .selectors import (
    START_POST_XPATHS,
    TEXTBOX_XPATHS,
    POST_BUTTON_XPATHS,
    CLOSE_POPUP_XPATHS,
)

def is_element_visible(driver, el):
    try:
        return driver.execute_script("""
            const el = arguments[0];
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
        """, el)
    except Exception:
        return False


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
                            time.sleep(1)
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
                    if el.is_displayed() and is_element_visible(driver, el):
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
        time.sleep(1)
    return None


def find_linkedin_textbox(driver, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            textbox = driver.execute_script("""
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

                function textOf(el) {
                    return (
                        (el.innerText || '') + ' ' +
                        (el.textContent || '') + ' ' +
                        (el.getAttribute('aria-label') || '') + ' ' +
                        (el.getAttribute('data-placeholder') || '') + ' ' +
                        (el.getAttribute('placeholder') || '')
                    ).toLowerCase();
                }

                // 1) direct editor candidates
                const directSelectors = [
                    "div[role='dialog'] [contenteditable='true']",
                    "div[role='dialog'] div[role='textbox']",
                    "div[role='dialog'] .ql-editor",
                    "[contenteditable='true'][role='textbox']",
                    "div[role='textbox'][contenteditable='true']",
                    ".ql-editor[contenteditable='true']",
                    "[contenteditable='true']",
                    "div[role='textbox']"
                ];

                for (const sel of directSelectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;
                        if (el.closest("[aria-hidden='true']")) continue;
                        return el;
                    }
                }

                // 2) placeholder-based search: locate visible text and then nearby editable node
                const allNodes = Array.from(document.querySelectorAll("*"));
                for (const node of allNodes) {
                    if (!isVisible(node)) continue;
                    const txt = textOf(node);

                    if (
                        txt.includes("what do you want to talk about") ||
                        txt.includes("talk about")
                    ) {
                        let cur = node;
                        for (let i = 0; i < 8 && cur; i++) {
                            const found = cur.querySelector(
                                "[contenteditable='true'], .ql-editor, div[role='textbox']"
                            );
                            if (found && isVisible(found)) {
                                return found;
                            }
                            cur = cur.parentElement;
                        }

                        // previous / next siblings fallback
                        let prev = node.previousElementSibling;
                        let next = node.nextElementSibling;

                        for (let i = 0; i < 5; i++) {
                            if (prev) {
                                const pFound = prev.querySelector?.("[contenteditable='true'], .ql-editor, div[role='textbox']");
                                if (pFound && isVisible(pFound)) return pFound;
                                prev = prev.previousElementSibling;
                            }
                            if (next) {
                                const nFound = next.querySelector?.("[contenteditable='true'], .ql-editor, div[role='textbox']");
                                if (nFound && isVisible(nFound)) return nFound;
                                next = next.nextElementSibling;
                            }
                        }

                        // if placeholder node itself is clickable, click it and retry active element
                        try { node.click(); } catch (e) {}
                    }
                }

                // 3) active element fallback
                const active = document.activeElement;
                if (active && isVisible(active)) {
                    if (active.isContentEditable || active.getAttribute('role') === 'textbox') {
                        return active;
                    }
                }

                return null;
            """)
            if textbox:
                print("✅ LinkedIn textbox found")
                try:
                    print("Textbox HTML:", textbox.get_attribute("outerHTML")[:500])
                except Exception:
                    pass
                return textbox
        except Exception as e:
            print("⚠️ find_linkedin_textbox JS error:", str(e))

        # click composer body once before retrying
        try:
            driver.execute_script("""
                const nodes = Array.from(document.querySelectorAll("*"));
                for (const el of nodes) {
                    const txt = ((el.innerText || '') + ' ' + (el.textContent || '')).toLowerCase();
                    if (txt.includes('what do you want to talk about') || txt.includes('talk about')) {
                        try { el.click(); } catch (e) {}
                        break;
                    }
                }
            """)
        except Exception:
            pass

        time.sleep(1)

    return None


def find_post_button(driver, timeout=15):
    end_time = time.time() + timeout
    while time.time() < end_time:
        el = _find_displayed(driver, POST_BUTTON_XPATHS, "Post button")
        if el:
            return el
        time.sleep(1)
    return None