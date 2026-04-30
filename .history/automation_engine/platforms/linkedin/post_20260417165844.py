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
                const selectors = [
                    'div[role="dialog"]',
                    'div.artdeco-modal',
                    '.share-box',
                    '.ql-editor',
                    'div[contenteditable="true"]',
                    'div[role="textbox"]',
                    'textarea'
                ];

                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const r = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        if (
                            r.width > 50 &&
                            r.height > 20 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden'
                        ) {
                            return true;
                        }
                    }
                }

                const bodyText = document.body.innerText || '';
                const markers = [
                    'What do you want to talk about?',
                    'Create a post',
                    'Post to anyone',
                    'Add a photo',
                    'Add a video'
                ];

                return markers.some(m => bodyText.includes(m));
            """)
            if opened:
                return True
        except:
            pass

        time.sleep(1)

    return False

# =========================
# FIND START POST BUTTON
# =========================
def find_start_post_button(driver, timeout=20):
    print("🔎 Locating real LinkedIn Start post trigger...")

    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(3)

    xpath_candidates = [
        "//button[contains(., 'Start a post')]",
        "//div[@role='button' and contains(., 'Start a post')]",
        "//button[contains(@class, 'share-box-feed-entry__trigger')]",
        "//div[contains(@class, 'share-box-feed-entry__trigger')]",
        "//span[contains(normalize-space(.), 'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(.), 'Start a post')]/ancestor::*[@role='button'][1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    print(f"✅ Start post button found using Selenium: {xpath}")
                    return el
        except:
            continue

    try:
        js_btn = driver.execute_script("""
            const nodes = Array.from(document.querySelectorAll('button, div[role="button"], span, div'));
            for (const node of nodes) {
                const text = (node.innerText || node.textContent || '').trim();
                if (text.includes('Start a post')) {
                    let cur = node;
                    for (let i = 0; i < 6 && cur; i++) {
                        const r = cur.getBoundingClientRect();
                        const style = window.getComputedStyle(cur);
                        const clickable =
                            cur.tagName === 'BUTTON' ||
                            cur.getAttribute('role') === 'button' ||
                            cur.onclick !== null;

                        if (
                            r.width > 40 &&
                            r.height > 20 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            clickable
                        ) {
                            return cur;
                        }
                        cur = cur.parentElement;
                    }
                }
            }
            return null;
        """)
        if js_btn:
            print("✅ Start post button found using JS fallback")
            return js_btn
    except Exception as e:
        print(f"❌ JS start button search failed: {e}")

    return None


# =========================
# ACTIVATE START POST
# =========================
def activate_start_post(driver, start_btn):
    print("⚡ Activating Start post with hit-test click...")

    remove_linkedin_overlay(driver)   # 👈 ADD THIS
    time.sleep(1)

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", start_btn)
        time.sleep(1)
    except:
        pass

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

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after elementFromPoint click")
            return True
    except Exception as e:
        print(f"❌ elementFromPoint click failed: {e}")

    try:
        start_btn.click()
        print("✅ Native click tried")

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after native click")
            return True
    except Exception as e:
        print(f"❌ Native click failed: {e}")

    try:
        ActionChains(driver).move_to_element(start_btn).pause(0.5).click().perform()
        print("✅ ActionChains click tried")

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after ActionChains click")
            return True
    except Exception as e:
        print(f"❌ ActionChains click failed: {e}")

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

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after deep child click")
            return True
    except Exception as e:
        print(f"❌ Deep child click failed: {e}")

    try:
        start_btn.send_keys(Keys.ENTER)
        print("✅ ENTER key tried")

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after ENTER key")
            return True
    except Exception as e:
        print(f"❌ ENTER key failed: {e}")

    try:
        start_btn.send_keys(Keys.SPACE)
        print("✅ SPACE key tried")

        if wait_for_composer_open(driver, timeout=4):
            print("✅ Composer/editor detected after SPACE key")
            return True
    except Exception as e:
        print(f"❌ SPACE key failed: {e}")

    return False


# =========================
# FIND REAL EDITOR
# =========================
def get_real_editor(driver, timeout=20):
    end_time = time.time() + timeout
    print("⏳ Waiting for LinkedIn editor...")

    while time.time() < end_time:
        try:
            editor = driver.execute_script("""
                const selectors = [
                    'div[role="dialog"] .ql-editor',
                    'div[role="dialog"] div[contenteditable="true"]',
                    'div[role="dialog"] div[role="textbox"]',

                    'div.artdeco-modal .ql-editor',
                    'div.artdeco-modal div[contenteditable="true"]',
                    'div.artdeco-modal div[role="textbox"]',

                    '.share-box .ql-editor',
                    '.share-box div[contenteditable="true"]',
                    '.share-box div[role="textbox"]',

                    '.ql-editor',
                    'div[contenteditable="true"]',
                    'div[role="textbox"]'
                ];

                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const r = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);

                        if (
                            r.width > 50 &&
                            r.height > 20 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden'
                        ) {
                            el.scrollIntoView({block:'center'});
                            el.focus();
                            return el;
                        }
                    }
                }
                return null;
            """)

            if editor:
                print("✅ Editor found")
                return editor

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

    try:
        textbox.click()
        time.sleep(0.5)
        textbox.send_keys(text)
        print("✅ Typed using send_keys")
        return True
    except:
        pass

    try:
        ActionChains(driver).move_to_element(textbox).click().pause(0.5).send_keys(text).perform()
        print("✅ Typed using ActionChains")
        return True
    except:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();
            el.innerHTML = '';
            el.textContent = text;

            el.dispatchEvent(new InputEvent('input', {
                bubbles: true,
                cancelable: true,
                inputType: 'insertText',
                data: text
            }));

            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: ' ' }));
            el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: ' ' }));
        """, textbox, text)

        print("✅ Typed using JS fallback")
        return True
    except Exception as e:
        print(f"❌ Typing failed: {e}")
        return False


# =========================
# FIND POST BUTTON
# =========================
def find_post_button(driver):
    xpath_candidates = [
        "//button[contains(@class,'share-actions__primary-action') and not(@disabled)]",
        "//button[@aria-label='Post' and not(@disabled)]",
        "//button[contains(@aria-label,'Post') and not(@disabled)]",
        "//span[normalize-space()='Post']/ancestor::button[1][not(@disabled)]",
        "//button[contains(., 'Post') and not(@disabled)]"
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for btn in elements:
                if btn.is_displayed() and btn.is_enabled():
                    print(f"✅ Post button found using: {xpath}")
                    return btn
        except:
            continue

    return None

def remove_linkedin_overlay(driver):
    try:
        driver.execute_script("""
            // remove main LinkedIn overlay
            const overlay = document.getElementById('interop-outlet');
            if (overlay) {
                overlay.style.display = 'none';
                overlay.remove();
            }

            // disable high z-index blockers
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (
                    (style.position === 'absolute' || style.position === 'fixed') &&
                    parseInt(style.zIndex) > 1000
                ) {
                    el.style.pointerEvents = 'none';
                }
            });
        """)
        print("🧹 LinkedIn overlay removed")
    except Exception as e:
        print("❌ Overlay removal error:", e)

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

        opened = activate_start_post(driver, start_btn)

        if not opened:
            save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {"success": False, "message": "Start post trigger found, but real composer did not open."}

        textbox = get_real_editor(driver, timeout=15)

        if not textbox:
            save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {"success": False, "message": "Composer opened, but textbox not found."}

        caption = str(post.caption).strip()
        typed = type_in_editor(driver, textbox, caption)

        if not typed:
            save_screenshot(driver, prefix="linkedin_typing_failed")
            return {"success": False, "message": "Textbox found, but typing failed."}

        print("✅ Caption entered")
        time.sleep(3)

        post_btn = find_post_button(driver)

        if not post_btn:
            save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {"success": False, "message": "Text entered, but Post button not found or disabled."}

        try:
            post_btn.click()
        except:
            driver.execute_script("arguments[0].click();", post_btn)

        print("✅ Post button clicked")
        time.sleep(5)

        return {"success": True, "message": "Post published successfully"}

    except Exception as e:
        save_screenshot(driver, prefix="linkedin_error")
        return {"success": False, "message": f"Automation Error: {str(e)}"}