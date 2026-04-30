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


def find_linkedin_textbox(driver, timeout=25):
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

                function getAllShadowRoots(root=document) {
                    const roots = [root];
                    const all = root.querySelectorAll ? Array.from(root.querySelectorAll("*")) : [];
                    for (const el of all) {
                        if (el.shadowRoot) roots.push(el.shadowRoot);
                    }
                    return roots;
                }

                function findInRoot(root) {
                    const selectors = [
                        "[contenteditable='true']",
                        "div[role='textbox']",
                        ".ql-editor",
                        "[data-placeholder]",
                        "[placeholder]"
                    ];

                    for (const sel of selectors) {
                        const nodes = Array.from(root.querySelectorAll(sel));
                        for (const el of nodes) {
                            if (!isVisible(el)) continue;

                            const txt = (
                                (el.innerText || '') + ' ' +
                                (el.textContent || '') + ' ' +
                                (el.getAttribute('aria-label') || '') + ' ' +
                                (el.getAttribute('data-placeholder') || '') + ' ' +
                                (el.getAttribute('placeholder') || '')
                            ).toLowerCase();

                            if (
                                el.isContentEditable ||
                                (el.getAttribute('contenteditable') === 'true') ||
                                el.getAttribute('role') === 'textbox' ||
                                txt.includes('what do you want to talk about') ||
                                txt.includes('talk about')
                            ) {
                                return el;
                            }
                        }
                    }

                    return null;
                }

                // 1. normal DOM + shadow roots
                const roots = getAllShadowRoots(document);
                for (const root of roots) {
                    const found = findInRoot(root);
                    if (found) return found;
                }

                // 2. click visible placeholder text and re-check active element
                const allNodes = Array.from(document.querySelectorAll("*"));
                for (const node of allNodes) {
                    if (!isVisible(node)) continue;
                    const txt = (
                        (node.innerText || '') + ' ' +
                        (node.textContent || '') + ' ' +
                        (node.getAttribute('aria-label') || '') + ' ' +
                        (node.getAttribute('data-placeholder') || '')
                    ).toLowerCase();

                    if (
                        txt.includes('what do you want to talk about') ||
                        txt.includes('talk about')
                    ) {
                        try { node.click(); } catch (e) {}
                        const active = document.activeElement;
                        if (active && isVisible(active)) {
                            if (active.isContentEditable || active.getAttribute('role') === 'textbox') {
                                return active;
                            }
                        }
                    }
                }

                // 3. fallback active element
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
            print("⚠️ main textbox finder failed:", str(e))

        # iframe fallback
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print("🧾 iframe fallback count:", len(iframes))

            for i, frame in enumerate(iframes):
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(frame)

                    candidates = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true'], div[role='textbox'], .ql-editor")
                    visible = [c for c in candidates if c.is_displayed()]
                    if visible:
                        print(f"✅ Textbox found in iframe index {i}")
                        tb = visible[0]
                        driver.switch_to.default_content()
                        driver.switch_to.frame(frame)
                        return tb
                except Exception:
                    continue

            driver.switch_to.default_content()
        except Exception as e:
            print("⚠️ iframe fallback failed:", str(e))
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

        time.sleep(1)

    return None


def find_post_button(driver, timeout=20):
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
                        r.width > 10 &&
                        r.height > 10 &&
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

                const selectors = [
                    "div[role='dialog'] [aria-label='Post']",
                    "div[role='dialog'] button",
                    "div[role='dialog'] [role='button']",
                    "[aria-label='Post']",
                    "button",
                    "[role='button']"
                ];

                for (const sel of selectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const node of nodes) {
                        if (!isVisible(node)) continue;

                        const txt = (
                            (node.innerText || '') + ' ' +
                            (node.textContent || '') + ' ' +
                            (node.getAttribute('aria-label') || '')
                        ).trim().toLowerCase();

                        if (
                            txt === 'post' ||
                            txt.includes(' post') ||
                            txt.startsWith('post') ||
                            node.getAttribute('aria-label') === 'Post'
                        ) {
                            if (isClickable(node)) return node;

                            let cur = node;
                            for (let i = 0; i < 5 && cur; i++) {
                                if (isClickable(cur)) return cur;
                                cur = cur.parentElement;
                            }
                        }
                    }
                }

                return null;
            """)
            if el:
                print("✅ Post button found using JS fallback")
                try:
                    print("Post button HTML:", el.get_attribute("outerHTML")[:500])
                except Exception:
                    pass
                return el
        except Exception as e:
            print("⚠️ Post button JS fallback failed:", str(e))

        time.sleep(1)

    return None