import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .selectors import (
    START_POST_XPATHS,
    TEXTBOX_XPATHS,
    POST_BUTTON_XPATHS,
    CLOSE_POPUP_XPATHS,
    PHOTO_BUTTON_XPATHS,
    FILE_INPUT_XPATHS,
    MEDIA_PREVIEW_XPATHS,
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

def find_photo_button(driver, timeout=15):
    end_time = time.time() + timeout
    while time.time() < end_time:
        el = _find_displayed(driver, PHOTO_BUTTON_XPATHS, "Photo button")
        if el:
            return el

        try:
            js_btn = driver.execute_script("""
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

                const nodes = Array.from(document.querySelectorAll("button, div[role='button'], span"));
                for (const el of nodes) {
                    if (!isVisible(el)) continue;
                    const text = (
                        (el.innerText || '') + ' ' +
                        (el.textContent || '') + ' ' +
                        (el.getAttribute('aria-label') || '')
                    ).toLowerCase();

                    if (
                        text.includes('photo') ||
                        text.includes('add media')
                    ) {
                        return el;
                    }
                }
                return null;
            """)
            if js_btn:
                print("✅ Photo button found using JS fallback")
                return js_btn
        except Exception as e:
            print("⚠️ find_photo_button JS fallback failed:", str(e))

        time.sleep(1)

    return None


def click_photo_button(driver, photo_btn):
    for action_name, action in [
        ("safe_click", lambda: safe_click(driver, photo_btn)),
        ("normal click", lambda: photo_btn.click()),
        ("js click", lambda: driver.execute_script("arguments[0].click();", photo_btn)),
    ]:
        try:
            result = action()
            if result is None or result is True:
                print(f"✅ Photo button clicked using {action_name}")
                return True
        except Exception as e:
            print(f"⚠️ Photo button {action_name} failed:", str(e))

    return False


def find_file_input(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            for xpath in FILE_INPUT_XPATHS:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        driver.execute_script("""
                            arguments[0].style.display = 'block';
                            arguments[0].style.visibility = 'visible';
                            arguments[0].style.opacity = '1';
                            arguments[0].removeAttribute('hidden');
                        """, el)
                    except Exception:
                        pass

                    print("✅ File input found")
                    return el
        except Exception as e:
            print("⚠️ find_file_input failed:", str(e))

        time.sleep(1)

    return None


def wait_for_media_preview(driver, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            for xpath in MEDIA_PREVIEW_XPATHS:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed() or is_element_visible(driver, el):
                            print(f"✅ Media preview detected using XPath: {xpath}")
                            return True
                    except Exception:
                        continue

            uploaded = driver.execute_script("""
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

                const imgs = Array.from(document.querySelectorAll("img"));
                for (const img of imgs) {
                    if (!isVisible(img)) continue;
                    const src = (img.src || '').toLowerCase();
                    if (src.includes('media') || src.includes('dms') || src.includes('image')) {
                        return true;
                    }
                }

                const nodes = Array.from(document.querySelectorAll("button, div, span"));
                for (const el of nodes) {
                    if (!isVisible(el)) continue;
                    const txt = (
                        (el.innerText || '') + ' ' +
                        (el.textContent || '') + ' ' +
                        (el.getAttribute('aria-label') || '')
                    ).toLowerCase();

                    if (
                        txt.includes('edit your photo') or
                        txt.includes('done') ||
                        txt.includes('uploaded')
                    ) {
                        return true;
                    }
                }

                return false;
            """)
            if uploaded:
                print("✅ Media preview detected using JS fallback")
                return True
        except Exception as e:
            print("⚠️ wait_for_media_preview failed:", str(e))

        time.sleep(1)

    return False


def upload_linkedin_image(driver, image_path, timeout=20):
    try:
        if not image_path:
            return {"success": False, "message": "No image path provided"}

        image_path = os.path.abspath(image_path)

        if not os.path.exists(image_path):
            return {"success": False, "message": f"Image file not found: {image_path}"}

        print("Finding Photo button...")
        photo_btn = find_photo_button(driver, timeout=timeout)
        if not photo_btn:
            return {"success": False, "message": "LinkedIn Photo button not found"}

        if not click_photo_button(driver, photo_btn):
            return {"success": False, "message": "LinkedIn Photo button click failed"}

        time.sleep(2)

        print("Finding file input...")
        file_input = find_file_input(driver, timeout=timeout)
        if not file_input:
            return {"success": False, "message": "LinkedIn file input not found"}

        file_input.send_keys(image_path)
        print("✅ Image path sent to file input:", image_path)

        print("Waiting for media preview...")
        if not wait_for_media_preview(driver, timeout=timeout):
            return {"success": False, "message": "LinkedIn image upload preview not detected"}

        time.sleep(2)
        return {"success": True, "message": "LinkedIn image uploaded successfully"}

    except Exception as e:
        print("❌ upload_linkedin_image error:", str(e))
        return {"success": False, "message": str(e)}

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


def find_post_button(driver, timeout=20, textbox=None):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            post_btn = driver.execute_script("""
                const textbox = arguments[0];

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

                function isEnabled(el) {
                    if (!el) return false;
                    return !el.disabled && el.getAttribute('aria-disabled') !== 'true';
                }

                function getText(el) {
                    return (
                        (el.innerText || '') + ' ' +
                        (el.textContent || '') + ' ' +
                        (el.getAttribute('aria-label') || '')
                    ).replace(/\\s+/g, ' ').trim().toLowerCase();
                }

                function isBadCandidate(el) {
                    const text = getText(el);
                    const html = (el.outerHTML || '').toLowerCase();

                    return (
                        text.includes('schedule post') ||
                        text === 'next' ||
                        text === 'back' ||
                        text.includes('open control menu') ||
                        text.includes('follow') ||
                        text.includes('comment') ||
                        text.includes('repost') ||
                        text.includes('like') ||
                        html.includes('open control menu')
                    );
                }

                function isPostCandidate(el) {
                    if (!el || !isVisible(el) || !isEnabled(el) || isBadCandidate(el)) {
                        return false;
                    }

                    const text = getText(el);
                    const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();

                    return (
                        text === 'post' ||
                        text === 'post post' ||
                        text.startsWith('post ') ||
                        text.endsWith(' post') ||
                        aria === 'post'
                    );
                }

                function nearestComposerRoot(start) {
                    let cur = start;
                    for (let i = 0; i < 12 && cur; i++) {
                        const buttons = Array.from(
                            cur.querySelectorAll ? cur.querySelectorAll("button, [role='button'], [aria-label]") : []
                        );
                        if (buttons.some(isPostCandidate)) {
                            return cur;
                        }
                        cur = cur.parentElement;
                    }
                    return null;
                }

                let root = null;

                if (textbox) {
                    root = nearestComposerRoot(textbox);
                }

                if (!root) {
                    const dialogs = Array.from(document.querySelectorAll("div[role='dialog']")).filter(isVisible);
                    if (dialogs.length) {
                        root = dialogs[dialogs.length - 1];
                    }
                }

                if (!root) {
                    root = document;
                }

                const candidates = Array.from(
                    root.querySelectorAll("button, [role='button'], [aria-label]")
                );

                for (const el of candidates) {
                    if (isPostCandidate(el)) {
                        return el;
                    }
                }

                return null;
            """, textbox)

            if post_btn:
                print("✅ Post button found")
                try:
                    print("Post button HTML:", post_btn.get_attribute("outerHTML")[:500])
                    print("Post button text:", (post_btn.text or "").strip())
                    print("Post button aria-label:", post_btn.get_attribute("aria-label"))
                except Exception:
                    pass
                return post_btn

        except Exception as e:
            print("⚠️ find_post_button failed:", str(e))

        time.sleep(1)

    return None