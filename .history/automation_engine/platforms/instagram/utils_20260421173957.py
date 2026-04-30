import time
from selenium.webdriver.common.by import By

from .selectors import (
    CREATE_BUTTON_XPATHS,
    NEW_POST_XPATHS,
    SELECT_FROM_COMPUTER_XPATHS,
    FILE_INPUT_XPATHS,
    NEXT_BUTTON_XPATHS,
    CAPTION_XPATHS,
    SHARE_BUTTON_XPATHS,
)


def wait_for_instagram_login(driver, timeout=180):
    print("👉 Waiting for Instagram login...")
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            current_url = driver.current_url.lower()
            body_text = driver.execute_script(
                "return (document.body.innerText || '').toLowerCase();"
            )

            print("Current URL:", current_url)

            if "accounts/login" not in current_url and "instagram.com" in current_url:
                print("✅ Instagram login detected")
                return True

            if (
                "challenge" in current_url
                or "two-factor" in current_url
                or "security code" in body_text
            ):
                print("⏳ Waiting for verification...")
        except Exception as e:
            print("⚠️ Login detection error:", str(e))

        time.sleep(2)

    print("❌ Login timeout")
    return False


def find_create_button(driver):
    xpaths = [
        "//a[contains(@href,'/create/select')]",
        "//a[@role='link' and @aria-label='Create']",
        "//span[normalize-space()='Create']/ancestor::a[1]",
        "//span[normalize-space()='Create']/ancestor::*[@role='button'][1]",
        "//div[@role='button' and @aria-label='Create']",
    ]

    for xpath in xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    print(f"✅ Create button found using XPath: {xpath}")
                    return el
        except Exception:
            continue
    return None


def find_new_post_button(driver):
    for xpath in NEW_POST_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except Exception:
            continue
    return None


def find_select_from_computer_button(driver):
    for xpath in SELECT_FROM_COMPUTER_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except Exception:
            continue
    return None


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


def click_next(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        # 1. XPath-based attempts
        xpaths = [
            "//button[normalize-space()='Next']",
            "//div[normalize-space()='Next']/ancestor::button[1]",
            "//span[normalize-space()='Next']/ancestor::button[1]",
            "//span[normalize-space()='Next']/ancestor::*[@role='button'][1]",
            "//div[@role='button'][.//span[normalize-space()='Next']]",
            "//button[contains(., 'Next')]",
            "//*[normalize-space(text())='Next']/ancestor::button[1]",
            "//*[normalize-space(text())='Next']/ancestor::*[@role='button'][1]",
        ]

        for xpath in xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if not el.is_displayed():
                            continue

                        print(f"✅ Next button found using XPath: {xpath}")
                        print("Next HTML:", el.get_attribute("outerHTML")[:500])

                        try:
                            el.click()
                            print("✅ Next clicked using selenium click")
                            time.sleep(3)
                            return True
                        except Exception:
                            pass

                        try:
                            driver.execute_script("arguments[0].click();", el)
                            print("✅ Next clicked using JS click")
                            time.sleep(3)
                            return True
                        except Exception:
                            pass

                    except Exception:
                        continue
            except Exception:
                continue

        # 2. JS exact-text scan
        try:
            clicked = driver.execute_script("""
                const visible = (el) => {
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
                };

                const nodes = Array.from(document.querySelectorAll("button, div[role='button'], span, div"));

                for (const node of nodes) {
                    const text = (node.innerText || node.textContent || '').trim().toLowerCase();
                    if (!visible(node)) continue;

                    if (text === 'next') {
                        node.click();
                        return true;
                    }
                }

                return false;
            """)
            if clicked:
                print("✅ Next clicked using JS exact-text fallback")
                time.sleep(3)
                return True
        except Exception as e:
            print("⚠️ Next JS exact-text fallback failed:", str(e))

        # 3. Hard fallback using Crop → nearest Next
        try:
            clicked = driver.execute_script("""
                const visible = (el) => {
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
                };

                const nodes = Array.from(document.querySelectorAll("button, div[role='button'], span, div"));
                let cropNode = null;
                let nextNode = null;

                for (const node of nodes) {
                    const text = (node.innerText || node.textContent || '').trim().toLowerCase();
                    if (!visible(node)) continue;

                    if (text === 'crop') cropNode = node;
                    if (text === 'next') nextNode = node;
                }

                if (nextNode) {
                    nextNode.click();
                    return true;
                }

                if (cropNode) {
                    let cur = cropNode.parentElement;
                    for (let i = 0; i < 5 && cur; i++) {
                        const candidates = Array.from(cur.querySelectorAll("button, div[role='button'], span, div"));
                        for (const c of candidates) {
                            const text = (c.innerText || c.textContent || '').trim().toLowerCase();
                            if (visible(c) && text === 'next') {
                                c.click();
                                return true;
                            }
                        }
                        cur = cur.parentElement;
                    }
                }

                return false;
            """)
            if clicked:
                print("✅ Next clicked using Crop/Next fallback")
                time.sleep(3)
                return True
        except Exception as e:
            print("⚠️ Crop/Next fallback failed:", str(e))

        try:
            preview = driver.execute_script(
                "return (document.body.innerText || '').slice(0, 1500);"
            )
            print("🧾 Instagram page preview after upload:", preview)
        except Exception:
            pass

        time.sleep(1)

    return False

def find_caption_box(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        for xpath in CAPTION_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed():
                            print(f"✅ Caption box found using XPath: {xpath}")
                            print("Caption HTML:", el.get_attribute("outerHTML")[:500])
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # JS fallback
        try:
            el = driver.execute_script("""
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 30 &&
                        r.height > 20 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                };

                const nodes = Array.from(document.querySelectorAll("textarea, div[contenteditable='true'], div[role='textbox'], div"));

                for (const node of nodes) {
                    const aria = (node.getAttribute('aria-label') || '').toLowerCase();
                    if (!visible(node)) continue;

                    if (
                        aria.includes('caption') ||
                        aria.includes('write a caption')
                    ) {
                        return node;
                    }
                }

                return null;
            """)
            if el:
                print("✅ Caption box found using JS fallback")
                print("Caption HTML:", el.get_attribute("outerHTML")[:500])
                return el
        except Exception as e:
            print("⚠️ Caption JS fallback failed:", str(e))

        try:
            preview = driver.execute_script(
                "return (document.body.innerText || '').slice(0, 1500);"
            )
            print("🧾 Instagram page preview at caption step:", preview)
        except Exception:
            pass

        time.sleep(1)

    return None

def find_share_button(driver, timeout=8):
    end_time = time.time() + timeout

    while time.time() < end_time:
        for xpath in SHARE_BUTTON_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        return el
            except Exception:
                continue
        time.sleep(1)

    return None