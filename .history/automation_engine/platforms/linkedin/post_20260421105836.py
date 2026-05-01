import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)

def short_pause(seconds=1.0):
    time.sleep(seconds)


def is_visible(driver, el):
    try:
        return driver.execute_script("""
            const el = arguments[0];
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
        """, el)
    except Exception:
        return False


def get_outer_html(driver, el, limit=500):
    try:
        html = driver.execute_script(
            "return arguments[0] && arguments[0].outerHTML ? arguments[0].outerHTML : '';",
            el
        )
        return html[:limit]
    except Exception:
        return ""


def safe_scroll_into_view(driver, el):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});",
            el
        )
        short_pause(0.7)
    except Exception:
        pass


def robust_click(driver, el, label="element"):
    click_methods = [
        ("safe_click", lambda: safe_click(driver, el)),
        ("selenium_click", lambda: el.click() or True),
        ("js_click", lambda: driver.execute_script("arguments[0].click();", el) or True),
        (
            "actionchains_click",
            lambda: ActionChains(driver).move_to_element(el).pause(0.4).click().perform() or True
        ),
        (
            "enter_key",
            lambda: (el.send_keys(Keys.ENTER), True)[1]
        ),
        (
            "space_key",
            lambda: (el.send_keys(Keys.SPACE), True)[1]
        ),
    ]

    for method_name, method in click_methods:
        try:
            safe_scroll_into_view(driver, el)
            result = method()
            print(f"✅ {label} clicked using {method_name}")
            if result is False:
                continue
            return True
        except Exception as e:
            print(f"⚠️ {label} click failed using {method_name}: {e}")

    return False


def remove_linkedin_overlay(driver):
    try:
        driver.execute_script("""
            const overlay = document.getElementById('interop-outlet');
            if (overlay) {
                overlay.style.display = 'none';
                overlay.remove();
            }

            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                const z = parseInt(style.zIndex);
                if (
                    (style.position === 'absolute' || style.position === 'fixed') &&
                    !Number.isNaN(z) &&
                    z > 1000
                ) {
                    el.style.pointerEvents = 'none';
                }
            });
        """)
        print("🧹 LinkedIn overlay removed")
    except Exception as e:
        print(f"⚠️ Overlay removal error: {e}")


def find_start_post_button(driver):
    for xpath in START_POST_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("✅ Start post button found using XPath:", xpath)
                        return el
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue
    return None


def wait_for_composer_surface(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            found = driver.execute_script("""
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 80 &&
                        r.height > 40 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                };

                const containers = [
                    ...document.querySelectorAll("div[role='dialog']"),
                    ...document.querySelectorAll("div.artdeco-modal"),
                    ...document.querySelectorAll(".share-box"),
                    ...document.querySelectorAll(".share-creation-state"),
                    ...document.querySelectorAll(".share-box-feed-entry")
                ].filter(visible);

                for (const box of containers) {
                    const txt = (box.innerText || "").toLowerCase();

                    const hasEditor = !!box.querySelector(`
                        .ql-editor[contenteditable="true"],
                        div[role="textbox"][contenteditable="true"],
                        div[contenteditable="true"],
                        textarea
                    `);

                    const hasMarkers =
                        txt.includes("what do you want to talk about") ||
                        txt.includes("post to anyone") ||
                        txt.includes("create a post") ||
                        txt.includes("add a photo") ||
                        txt.includes("add a video");

                    if (hasEditor || hasMarkers) {
                        return true;
                    }
                }

                return false;
            """)
            if found:
                print("✅ Composer surface detected")
                return True
        except Exception:
            pass

        short_pause(1)

    return False


def score_textbox_candidate(driver, el):
    try:
        data = driver.execute_script("""
            const el = arguments[0];
            const parent = el.closest(
                "div[role='dialog'], div.artdeco-modal, .share-box, .share-creation-state, .share-box-feed-entry"
            );

            const own = (
                (el.getAttribute('aria-label') || '') + ' ' +
                (el.getAttribute('placeholder') || '') + ' ' +
                (el.className || '')
            ).toLowerCase();

            const parentText = parent ? (parent.innerText || '').toLowerCase() : '';

            let score = 0;
            if (parent) score += 5;
            if (el.isContentEditable) score += 4;
            if ((el.getAttribute('role') || '').toLowerCase() === 'textbox') score += 3;
            if ((el.className || '').toLowerCase().includes('ql-editor')) score += 4;
            if (parentText.includes('what do you want to talk about')) score += 5;
            if (parentText.includes('post to anyone')) score += 5;
            if (parentText.includes('create a post')) score += 4;
            if (parentText.includes('add a photo')) score += 2;
            if (parentText.includes('add a video')) score += 2;

            return {
                own,
                parentText: parentText.slice(0, 300),
                score
            };
        """, el)

        own = data.get("own", "")
        if any(x in own for x in ["search", "message", "comment", "chat"]):
            return -1, data
        return data.get("score", 0), data
    except Exception:
        return -1, {}


def find_real_textbox(driver):
    candidates = []

    for selector in TEXTBOX_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if not is_visible(driver, el):
                        continue
                    score, meta = score_textbox_candidate(driver, el)
                    if score < 0:
                        continue
                    candidates.append((score, selector, el, meta))
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    if not candidates:
        print("⚠️ No textbox candidates found")
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_selector, best_el, best_meta = candidates[0]
    safe_scroll_into_view(driver, best_el)

    try:
        driver.execute_script("arguments[0].focus();", best_el)
    except Exception:
        pass

    print("✅ Textbox found using CSS:", best_selector)
    print("⭐ Textbox score:", best_score)
    print("📝 Textbox hint:", best_meta.get("own", ""))
    return best_el


def activate_and_focus_composer(driver):
    textbox = find_real_textbox(driver)
    if textbox:
        robust_click(driver, textbox, label="textbox")
        short_pause(1)
        return textbox

    try:
        activated = driver.execute_script("""
            const visible = (el) => {
                if (!el) return false;
                const r = el.getBoundingClientRect();
                const s = window.getComputedStyle(el);
                return (
                    r.width > 120 &&
                    r.height > 80 &&
                    s.display !== 'none' &&
                    s.visibility !== 'hidden' &&
                    s.opacity !== '0'
                );
            };

            const containers = [
                ...document.querySelectorAll("div[role='dialog']"),
                ...document.querySelectorAll("div.artdeco-modal"),
                ...document.querySelectorAll(".share-box"),
                ...document.querySelectorAll(".share-creation-state"),
                ...document.querySelectorAll(".share-box-feed-entry")
            ].filter(visible);

            for (const box of containers) {
                const editor = box.querySelector(`
                    .ql-editor[contenteditable="true"],
                    div[role="textbox"][contenteditable="true"],
                    div[contenteditable="true"],
                    textarea
                `);

                if (editor) {
                    editor.focus();
                    editor.click();
                    return true;
                }

                box.click();
                box.focus();
                return true;
            }

            return false;
        """)
        print("Composer activation fallback:", activated)
    except Exception as e:
        print("⚠️ Composer activation JS error:", str(e))

    short_pause(1)
    return find_real_textbox(driver)


def type_into_element(driver, element, caption):
    try:
        driver.execute_script("arguments[0].focus();", element)
        short_pause(0.4)
    except Exception:
        pass

    try:
        element.click()
    except Exception:
        pass

    try:
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
    except Exception:
        pass

    methods = [
        ("send_keys", lambda: element.send_keys(caption) or True),
        (
            "actionchains",
            lambda: ActionChains(driver).move_to_element(element).click().pause(0.4).send_keys(caption).perform() or True
        ),
        (
            "js_fallback",
            lambda: driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if (el.tagName === 'TEXTAREA' || 'value' in el) {
                    el.value = text;
                } else {
                    el.textContent = '';
                    el.innerHTML = '';
                    el.textContent = text;
                }

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            """, element, caption)
        )
    ]

    for method_name, method in methods:
        try:
            method()
            print(f"✅ Caption typed using {method_name}")
            short_pause(1)

            typed_text = driver.execute_script("""
                const el = arguments[0];
                return (el.innerText || el.textContent || el.value || '').trim();
            """, element)
            print("📝 Text inside editor:", typed_text[:300])

            if caption.strip() and caption.strip().lower() in typed_text.strip().lower():
                return True

            if typed_text.strip():
                return True
        except Exception as e:
            print(f"⚠️ Typing failed using {method_name}: {e}")

    return False


def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("✅ Post button found using CSS:", selector)
                        return btn
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action')]",
        "//button[@aria-label='Post']",
        "//button[contains(@aria-label,'Post')]",
        "//span[normalize-space()='Post']/ancestor::button[1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("✅ Post button found using XPath:", xpath)
                        return btn
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    return None


def verify_post_success(driver, caption, timeout=12):
    end_time = time.time() + timeout
    expected = (caption or "").strip().lower()

    while time.time() < end_time:
        try:
            confirmed = driver.execute_script("""
                const expected = arguments[0];
                const bodyText = (document.body.innerText || '').toLowerCase();

                const successMarkers = [
                    'your post is now live',
                    'your post is live',
                    'post shared',
                    'shared your post',
                    'post successful'
                ];

                if (successMarkers.some(x => bodyText.includes(x))) {
                    return true;
                }

                const dialogs = Array.from(document.querySelectorAll('div[role="dialog"], div.artdeco-modal'))
                    .filter(d => {
                        const r = d.getBoundingClientRect();
                        const s = window.getComputedStyle(d);
                        return r.width > 50 && r.height > 20 &&
                               s.display !== 'none' && s.visibility !== 'hidden';
                    });

                if (dialogs.length === 0 && expected && bodyText.includes(expected)) {
                    return true;
                }

                return false;
            """, expected)

            if confirmed:
                return True
        except Exception:
            pass

        short_pause(1)

    return False


def post_to_linkedin(driver, post):
    try:
        caption = str(post.caption).strip()

        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)
        medium_pause()
        remove_linkedin_overlay(driver)

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        print("Start trigger HTML:", get_outer_html(driver, start_post_button))

        clicked = robust_click(driver, start_post_button, label="start post button")
        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed. Screenshot: {screenshot}"
            }

        short_pause(2)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        opened = wait_for_composer_surface(driver, timeout=10)
        if not opened:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_detected")
            return {
                "success": False,
                "message": f"LinkedIn composer not detected. Screenshot: {screenshot}"
            }

        textbox = activate_and_focus_composer(driver)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        print("Focused textbox HTML:", get_outer_html(driver, textbox))

        typed = type_into_element(driver, textbox, caption)
        if not typed:
            try:
                ActionChains(driver).send_keys(Keys.TAB).perform()
                short_pause(1)
                textbox = find_real_textbox() or textbox
                typed = type_into_element(driver, textbox, caption)
            except Exception:
                pass

        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        short_pause(2)
        medium_pause()

        post_button = None
        for _ in range(3):
            post_button = find_post_button(driver)
            if post_button:
                break
            short_pause(1.5)

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        print("Post button HTML:", get_outer_html(driver, post_button))

        clicked = robust_click(driver, post_button, label="post button")
        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"LinkedIn post button click failed. Screenshot: {screenshot}"
            }

        print("Post button clicked")
        short_pause(8)

        confirmed = verify_post_success(driver, caption, timeout=12)
        if confirmed:
            print("✅ Post published on LinkedIn")
            return {
                "success": True,
                "message": "Post published on LinkedIn"
            }

        screenshot = save_screenshot(driver, prefix="linkedin_post_not_confirmed")
        return {
            "success": False,
            "message": f"Post click happened, but success was not confirmed. Screenshot: {screenshot}"
        }

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }