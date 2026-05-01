import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.screenshot_helper import save_screenshot


# =========================
# WAIT UNTIL COMPOSER REALLY OPENS
# =========================
def wait_for_composer_open(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            opened = driver.execute_script("""
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 120 &&
                        r.height > 60 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                };

                const containers = [
                    ...document.querySelectorAll('div[role="dialog"]'),
                    ...document.querySelectorAll('div.artdeco-modal'),
                    ...document.querySelectorAll('.share-box'),
                    ...document.querySelectorAll('.share-creation-state'),
                    ...document.querySelectorAll('.share-box-feed-entry')
                ].filter(visible);

                for (const box of containers) {
                    const text = (box.innerText || '').toLowerCase();

                    const hasEditor = !!box.querySelector(`
                        .ql-editor[contenteditable="true"],
                        div[role="textbox"][contenteditable="true"],
                        div[contenteditable="true"],
                        textarea
                    `);

                    const hasMarkers =
                        text.includes('create a post') ||
                        text.includes('what do you want to talk about') ||
                        text.includes('post to anyone') ||
                        text.includes('add a photo') ||
                        text.includes('add a video');

                    if (hasEditor || hasMarkers) {
                        return true;
                    }
                }

                return false;
            """)
            if opened:
                return True
        except:
            pass

        time.sleep(1)

    return False


# =========================
# REMOVE LINKEDIN OVERLAY
# =========================
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
        print(f"❌ Overlay removal error: {e}")


# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver, timeout=20):
    print("🔎 Locating real LinkedIn Start post trigger...")

    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(3)

    exact_selectors = [
        (By.CSS_SELECTOR, "div[aria-label='Start a post']"),
        (By.CSS_SELECTOR, "[componentkey='draft-text']"),
        (By.XPATH, "//*[@aria-label='Start a post']"),
        (By.XPATH, "//*[contains(@componentkey, 'draft-text')]"),
        (By.XPATH, "//div[@role='button' and @aria-label='Start a post']"),
        (By.XPATH, "//div[@role='button' and contains(., 'Start a post')]"),
    ]

    for by, selector in exact_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for el in elements:
                if el.is_displayed():
                    print(f"✅ Start post trigger found using exact selector: {selector}")
                    return el
        except Exception:
            continue

    try:
        js_btn = driver.execute_script("""
            const candidates = Array.from(document.querySelectorAll(
                "div[aria-label='Start a post'], [componentkey='draft-text'], div[role='button'], button, span, div"
            ));

            for (const el of candidates) {
                const text = (el.innerText || el.textContent || '').trim();
                const aria = (el.getAttribute('aria-label') || '').trim();
                const componentKey = (el.getAttribute('componentkey') || '').trim();
                const r = el.getBoundingClientRect();
                const s = window.getComputedStyle(el);

                const visible =
                    r.width > 40 &&
                    r.height > 20 &&
                    s.display !== 'none' &&
                    s.visibility !== 'hidden';

                const looksRight =
                    aria === 'Start a post' ||
                    componentKey === 'draft-text' ||
                    text === 'Start a post';

                if (visible && looksRight) {
                    return el;
                }
            }
            return null;
        """)
        if js_btn:
            print("✅ Start post trigger found using JS exact fallback")
            return js_btn
    except Exception as e:
        print(f"❌ JS start trigger search failed: {e}")

    return None

# =========================
# ACTIVATE START POST
# =========================
def activate_start_post(driver, start_btn):
    print("⚡ Activating Start post with hit-test click...")

    remove_linkedin_overlay(driver)
    time.sleep(1)

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_btn)
        time.sleep(1)
    except:
        pass

    try:
        driver.execute_script("arguments[0].click();", start_btn)
        print("✅ Direct JS click tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after direct JS click")
            return True
    except Exception as e:
        print(f"❌ Direct JS click failed: {e}")

    try:
        clicked = driver.execute_script("""
            const root = arguments[0];
            const rect = root.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;

            const real = document.elementFromPoint(x, y);
            if (!real) return "no-element";

            real.dispatchEvent(new MouseEvent('mouseover', {bubbles:true, clientX:x, clientY:y}));
            real.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:x, clientY:y}));
            real.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:x, clientY:y}));
            real.dispatchEvent(new MouseEvent('click', {bubbles:true, clientX:x, clientY:y}));

            return real.outerHTML ? real.outerHTML.slice(0, 300) : real.tagName;
        """, start_btn)

        print(f"✅ Hit-test click target: {clicked}")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after hit-test click")
            return True
    except Exception as e:
        print(f"❌ Hit-test click failed: {e}")

    try:
        rect = start_btn.rect
        ActionChains(driver).move_to_element_with_offset(
            start_btn,
            max(1, int(rect["width"] / 2) - 2),
            max(1, int(rect["height"] / 2) - 2)
        ).click().perform()

        print("✅ Center offset click tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after center offset click")
            return True
    except Exception as e:
        print(f"❌ Center offset click failed: {e}")

    try:
        driver.execute_script("""
            const root = arguments[0];
            const rect = root.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const real = document.elementFromPoint(x, y);
            if (real) real.click();
        """, start_btn)

        print("✅ elementFromPoint().click() tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after elementFromPoint click")
            return True
    except Exception as e:
        print(f"❌ elementFromPoint click failed: {e}")

    try:
        start_btn.click()
        print("✅ Native click tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after native click")
            return True
    except Exception as e:
        print(f"❌ Native click failed: {e}")

    try:
        ActionChains(driver).move_to_element(start_btn).pause(0.5).click().perform()
        print("✅ ActionChains click tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after ActionChains click")
            return True
    except Exception as e:
        print(f"❌ ActionChains click failed: {e}")

    try:
        clicked = driver.execute_script("""
            let el = arguments[0];
            for (let i = 0; i < 5 && el; i++) {
                try {
                    el.click();
                    return i;
                } catch(e) {}
                el = el.parentElement;
            }
            return -1;
        """, start_btn)

        print(f"✅ Parent chain click tried, level: {clicked}")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after parent chain click")
            return True
    except Exception as e:
        print(f"❌ Parent chain click failed: {e}")

    try:
        driver.execute_script("""
            const root = arguments[0];
            const candidates = root.querySelectorAll('button, span, div');
            for (const c of candidates) {
                const text = (c.innerText || c.textContent || '').trim();
                const r = c.getBoundingClientRect();
                if (text.includes('Start a post') && r.width > 20 && r.height > 10) {
                    c.click();
                    return true;
                }
            }
            root.click();
            return true;
        """, start_btn)

        print("✅ Deep child click tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after deep child click")
            return True
    except Exception as e:
        print(f"❌ Deep child click failed: {e}")

    try:
        start_btn.send_keys(Keys.ENTER)
        print("✅ ENTER key tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after ENTER key")
            return True
    except Exception as e:
        print(f"❌ ENTER key failed: {e}")

    try:
        start_btn.send_keys(Keys.SPACE)
        print("✅ SPACE key tried")
        print("📍 Current URL after click:", driver.current_url)
        print("📄 Current title after click:", driver.title)

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after SPACE key")
            return True
    except Exception as e:
        print(f"❌ SPACE key failed: {e}")

    try:
        page_preview = driver.execute_script("""
            return (document.body.innerText || '').slice(0, 2000);
        """)
        print("🧾 Page preview after Start post click:", page_preview)
    except Exception as e:
        print(f"❌ Could not capture page preview: {e}")

    save_screenshot(driver, prefix="linkedin_after_start_post_click")
    return False


# =========================
# FIND REAL EDITOR
# =========================
def get_real_editor(driver, timeout=20):
    end_time = time.time() + timeout
    print("⏳ Waiting for LinkedIn editor...")

    while time.time() < end_time:
        try:
            result = driver.execute_script("""
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 80 &&
                        r.height > 24 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                };

                const editable = (el) => {
                    return !!el && (
                        el.isContentEditable ||
                        el.getAttribute('contenteditable') === 'true' ||
                        el.tagName === 'TEXTAREA'
                    );
                };

                const badHint = (txt) => {
                    txt = (txt || '').toLowerCase();
                    return (
                        txt.includes('search') ||
                        txt.includes('message') ||
                        txt.includes('comment') ||
                        txt.includes('chat') ||
                        txt.includes('caption')
                    );
                };

                const selectors = [
                    'div[role="dialog"] .ql-editor[contenteditable="true"]',
                    'div[role="dialog"] div[role="textbox"][contenteditable="true"]',
                    'div[role="dialog"] div[contenteditable="true"]',
                    'div[role="dialog"] textarea',

                    'div.artdeco-modal .ql-editor[contenteditable="true"]',
                    'div.artdeco-modal div[role="textbox"][contenteditable="true"]',
                    'div.artdeco-modal div[contenteditable="true"]',
                    'div.artdeco-modal textarea',

                    '.share-box .ql-editor[contenteditable="true"]',
                    '.share-box div[role="textbox"]',
                    '.share-box div[contenteditable="true"]',
                    '.share-box textarea',

                    '.share-creation-state .ql-editor[contenteditable="true"]',
                    '.share-creation-state div[role="textbox"]',
                    '.share-creation-state div[contenteditable="true"]',
                    '.share-creation-state textarea',

                    '.share-box-feed-entry .ql-editor[contenteditable="true"]',
                    '.share-box-feed-entry div[role="textbox"]',
                    '.share-box-feed-entry div[contenteditable="true"]',
                    '.share-box-feed-entry textarea',

                    '.ql-editor[contenteditable="true"]',
                    'div[role="textbox"][contenteditable="true"]',
                    'div[contenteditable="true"]',
                    'textarea'
                ];

                const candidates = [];

                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        if (!visible(el) || !editable(el)) continue;

                        const ownText = (
                            (el.getAttribute('aria-label') || '') + ' ' +
                            (el.getAttribute('placeholder') || '') + ' ' +
                            (el.className || '')
                        ).toLowerCase();

                        if (badHint(ownText)) continue;

                        const parent = el.closest('div[role="dialog"], div.artdeco-modal, .share-box, .share-creation-state, .share-box-feed-entry');
                        const parentText = parent ? (parent.innerText || '').toLowerCase() : '';

                        let score = 0;

                        if (parent) score += 5;
                        if (el.className && String(el.className).toLowerCase().includes('ql-editor')) score += 4;
                        if ((el.getAttribute('role') || '').toLowerCase() === 'textbox') score += 3;
                        if (el.isContentEditable) score += 3;
                        if (parentText.includes('create a post')) score += 4;
                        if (parentText.includes('what do you want to talk about')) score += 4;
                        if (parentText.includes('post to anyone')) score += 4;
                        if (parentText.includes('add a photo')) score += 2;
                        if (parentText.includes('add a video')) score += 2;

                        candidates.push({
                            el,
                            selector: sel,
                            score,
                            ownText: ownText.slice(0, 200),
                            parentText: parentText.slice(0, 300)
                        });
                    }
                }

                candidates.sort((a, b) => b.score - a.score);

                if (candidates.length) {
                    const best = candidates[0];
                    best.el.scrollIntoView({block:'center'});
                    best.el.focus();

                    return {
                        found: true,
                        selector: best.selector,
                        score: best.score,
                        ownText: best.ownText,
                        parentText: best.parentText,
                        element: best.el
                    };
                }

                return {
                    found: false,
                    debug: Array.from(document.querySelectorAll('[contenteditable="true"], textarea, div[role="textbox"]'))
                        .slice(0, 15)
                        .map(el => ({
                            tag: el.tagName,
                            role: el.getAttribute('role') || '',
                            aria: el.getAttribute('aria-label') || '',
                            placeholder: el.getAttribute('placeholder') || '',
                            cls: (el.className || '').toString().slice(0, 120),
                            text: (el.innerText || '').slice(0, 120)
                        }))
                };
            """)

            if result and result.get("found"):
                print("✅ Editor found")
                print("🧭 Best selector:", result.get("selector"))
                print("⭐ Score:", result.get("score"))
                print("📝 Editor hint:", result.get("ownText"))
                return driver.execute_script("return arguments[0];", result["element"])

            if result and result.get("debug") is not None:
                print("⚠️ No editor found. Debug candidates:", result.get("debug"))

        except Exception as e:
            print(f"❌ Editor search error: {e}")

        time.sleep(1)

    return None


# =========================
# TYPE TEXT INTO EDITOR
# =========================
def type_in_editor(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(1)
    except:
        pass

    typed = False

    try:
        textbox.click()
        time.sleep(0.5)
        textbox.send_keys(text)
        print("✅ Typed using send_keys")
        typed = True
    except:
        pass

    if not typed:
        try:
            ActionChains(driver).move_to_element(textbox).click().pause(0.5).send_keys(text).perform()
            print("✅ Typed using ActionChains")
            typed = True
        except:
            pass

    if not typed:
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if (el.tagName === 'TEXTAREA') {
                    el.value = text;
                } else {
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
            """, textbox, text)
            print("✅ Typed using JS fallback")
            typed = True
        except Exception as e:
            print(f"❌ Typing failed: {e}")
            return False

    try:
        driver.execute_script("""
            const el = arguments[0];
            const actualText = arguments[1];

            el.focus();
            el.dispatchEvent(new InputEvent('input', {
                bubbles: true,
                cancelable: true,
                data: actualText
            }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: ' ' }));
            el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: ' ' }));
            el.blur();
        """, textbox, text)
        print("✅ Input/change/blur events dispatched")
    except Exception as e:
        print(f"❌ Event dispatch failed: {e}")

    time.sleep(2)
    return True


# =========================
# FIND POST BUTTON
# =========================
def find_post_button(driver, timeout=10):
    end_time = time.time() + timeout
    print("🔎 Searching for enabled Post button inside composer...")

    while time.time() < end_time:
        try:
            btn = driver.execute_script("""
                const containers = Array.from(document.querySelectorAll(
                    'div[role="dialog"], div.artdeco-modal, .share-box, .share-creation-state, .share-box-feed-entry'
                ));

                for (const container of containers) {
                    const r = container.getBoundingClientRect();
                    const s = window.getComputedStyle(container);
                    const visible =
                        r.width > 100 &&
                        r.height > 100 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden';

                    if (!visible) continue;

                    const buttons = Array.from(container.querySelectorAll('button'));

                    const candidate = buttons.find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        const aria = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                        const br = btn.getBoundingClientRect();
                        const bs = window.getComputedStyle(btn);
                        const visibleBtn =
                            br.width > 40 &&
                            br.height > 20 &&
                            bs.display !== 'none' &&
                            bs.visibility !== 'hidden';

                        const enabled =
                            !btn.disabled &&
                            btn.getAttribute('aria-disabled') !== 'true';

                        return visibleBtn && enabled &&
                               (
                                   text === 'post' ||
                                   aria === 'post' ||
                                   aria.includes('post')
                               );
                    });

                    if (candidate) return candidate;
                }

                return null;
            """)
            if btn:
                print("✅ Composer Post button found")
                return btn
        except Exception as e:
            print(f"❌ Post button search error: {e}")

        time.sleep(1)

    return None


def verify_post_by_text(driver, caption, timeout=15):
    end_time = time.time() + timeout
    expected = (caption or "").strip().lower()

    while time.time() < end_time:
        try:
            found = driver.execute_script("""
                const expected = arguments[0];

                const dialogs = Array.from(document.querySelectorAll('div[role="dialog"], div.artdeco-modal'))
                    .filter(d => {
                        const r = d.getBoundingClientRect();
                        const s = window.getComputedStyle(d);
                        return (
                            r.width > 50 &&
                            r.height > 20 &&
                            s.display !== 'none' &&
                            s.visibility !== 'hidden'
                        );
                    });

                if (dialogs.length > 0) {
                    return false;
                }

                const bodyText = (document.body.innerText || '').toLowerCase();
                return !!expected && bodyText.includes(expected);
            """, expected)

            if found:
                return True
        except:
            pass

        time.sleep(1)

    return False


# =========================
# MAIN FUNCTION
# =========================
def post_to_linkedin(driver, post):
    try:
        print("Calling LinkedIn automation...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)

        remove_linkedin_overlay(driver)
        time.sleep(2)

        print("🖱️ Searching for Start Post trigger...")
        start_btn = find_start_post_button(driver, timeout=20)

        if not start_btn:
            save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {"success": False, "message": "Start post button not found."}

        textbox = None
        opened = activate_start_post(driver, start_btn)

        if not opened:
            print("⚠️ Composer not detected by first check, trying direct editor search once...")
            textbox = get_real_editor(driver, timeout=5)
            if textbox:
                print("✅ Editor found even though composer marker was missed")
                opened = True
            else:
                save_screenshot(driver, prefix="linkedin_composer_not_opened")
                return {"success": False, "message": "Start post trigger found, but real composer did not open."}

        if opened and not textbox:
            textbox = get_real_editor(driver, timeout=20)

        if not textbox:
            save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": "Composer opened, but textbox not found."}

        try:
            editor_ok = driver.execute_script("""
                const el = arguments[0];
                const parent = el.closest('div[role="dialog"], div.artdeco-modal, .share-box, .share-creation-state, .share-box-feed-entry');

                const txt = (
                    (el.getAttribute('aria-label') || '') + ' ' +
                    (el.getAttribute('placeholder') || '') + ' ' +
                    (el.className || '')
                ).toLowerCase();

                const parentTxt = parent
                    ? (
                        (parent.getAttribute('class') || '') + ' ' +
                        (parent.innerText || '')
                    ).toLowerCase()
                    : '';

                const bodyText = (document.body.innerText || '').toLowerCase();

                return (
                    el.isContentEditable ||
                    txt.includes('editor') ||
                    txt.includes('textbox') ||
                    txt.includes('ql-editor') ||
                    txt.includes('contenteditable') ||

                    parentTxt.includes('post') ||
                    parentTxt.includes('share') ||
                    parentTxt.includes('create a post') ||
                    parentTxt.includes('post to anyone') ||

                    bodyText.includes('create a post') ||
                    bodyText.includes('what do you want to talk about') ||
                    bodyText.includes('post to anyone') ||
                    bodyText.includes('add a photo') ||
                    bodyText.includes('add a video')
                );
            """, textbox)
            print("✅ Editor validation:", editor_ok)
        except Exception as e:
            print("❌ Editor validation JS failed:", e)
            editor_ok = False

        try:
            editor_html = driver.execute_script("""
                const el = arguments[0];
                return el.outerHTML ? el.outerHTML.slice(0, 1000) : 'No outerHTML';
            """, textbox)
            print("🧾 Editor outerHTML preview:", editor_html)
        except Exception as e:
            print("❌ Could not capture editor outerHTML:", e)

        if not editor_ok:
            save_screenshot(driver, prefix="linkedin_invalid_editor")
            return {"success": False, "message": "Detected editor is not LinkedIn post composer."}

        caption = str(post.caption).strip()
        typed = type_in_editor(driver, textbox, caption)

        if not typed:
            save_screenshot(driver, prefix="linkedin_typing_failed")
            return {"success": False, "message": "Textbox found, but typing failed."}

        try:
            typed_text = driver.execute_script("""
                const el = arguments[0];
                return (el.innerText || el.textContent || el.value || '').trim();
            """, textbox)
            print("📝 Text inside editor after typing:", typed_text)
        except Exception as e:
            print("❌ Could not read typed text:", e)

        print("✅ Caption entered")
        time.sleep(4)

        post_btn = find_post_button(driver, timeout=5)

        if not post_btn:
            print("⚠️ Post button not ready yet, trying one extra editor wake-up...")
            try:
                driver.execute_script("""
                    const el = arguments[0];
                    el.focus();
                    el.dispatchEvent(new InputEvent('input', {
                        bubbles: true,
                        cancelable: true,
                        data: '!'
                    }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: '!' }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: '!' }));
                    el.blur();
                """, textbox)
            except:
                pass

            time.sleep(2)
            post_btn = find_post_button(driver, timeout=5)

        if not post_btn:
            save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {"success": False, "message": "Text entered, but Post button not found or disabled."}

        try:
            post_btn.click()
        except:
            driver.execute_script("""
                const btn = arguments[0];
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                btn.dispatchEvent(new MouseEvent('click', {bubbles:true}));
            """, post_btn)

        print("✅ Post button clicked")
        time.sleep(8)

        text_verified = verify_post_by_text(driver, caption, timeout=10)
        if text_verified:
            print("✅ POST VERIFIED BY TEXT")
            return {"success": True, "message": "Post published successfully"}

        confirmed = False
        try:
            confirmed = driver.execute_script("""
                const bodyText = (document.body.innerText || '').toLowerCase();

                const successMarkers = [
                    'your post is now live',
                    'your post is live',
                    'post shared',
                    'shared your post',
                    'post successful'
                ];

                return successMarkers.some(x => bodyText.includes(x));
            """)
        except Exception as e:
            print("❌ Confirmation JS failed:", e)
            confirmed = False

        if confirmed:
            print("✅ POST SUCCESSFULLY CREATED")
            return {"success": True, "message": "Post published successfully"}

        save_screenshot(driver, prefix="linkedin_post_clicked_but_not_confirmed")
        return {"success": False, "message": "Post button clicked, but post was not confirmed live."}

    except Exception as e:
        save_screenshot(driver, prefix="linkedin_error")
        return {"success": False, "message": f"Automation Error: {str(e)}"}