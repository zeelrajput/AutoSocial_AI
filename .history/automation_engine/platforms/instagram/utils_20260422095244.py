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


def click_next(driver, timeout=15):
    end_time = time.time() + timeout

    def get_page_text():
        try:
            return driver.execute_script(
                "return (document.body.innerText || '').toLowerCase();"
            )
        except Exception:
            return ""

    while time.time() < end_time:
        before_text = get_page_text()

        next_candidates = []

        xpaths = [
            "//div[@role='dialog']//button[normalize-space()='Next']",
            "//div[@role='dialog']//*[normalize-space()='Next']/ancestor::button[1]",
            "//div[@role='dialog']//*[normalize-space()='Next']/ancestor::*[@role='button'][1]",
            "//button[normalize-space()='Next']",
            "//*[normalize-space()='Next']/ancestor::button[1]",
            "//*[normalize-space()='Next']/ancestor::*[@role='button'][1]",
        ]

        for xpath in xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            next_candidates.append((xpath, el))
                    except Exception:
                        continue
            except Exception:
                continue

        for xpath, el in next_candidates:
            try:
                print(f"✅ Trying Next button with XPath: {xpath}")
                print("Next HTML:", el.get_attribute("outerHTML")[:500])

                try:
                    el.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", el)
                    except Exception:
                        continue

                time.sleep(3)

                after_text = get_page_text()

                # verify screen changed
                if after_text != before_text:
                    print("✅ Next click caused page/modal change")
                    return True

                # explicit success states
                if (
                    "write a caption" in after_text
                    or "share" in after_text
                    or "accessibility" in after_text
                    or "advanced settings" in after_text
                ):
                    print("✅ Reached caption/share step")
                    return True

                print("⚠️ Next clicked but step did not change")
            except Exception:
                continue

        try:
            preview = driver.execute_script(
                "return (document.body.innerText || '').slice(0, 1500);"
            )
            print("🧾 Instagram page preview while clicking Next:", preview)
        except Exception:
            pass

        time.sleep(1)

    return False


def find_caption_box(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
        # 1. XPath search
        for xpath in CAPTION_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if not el.is_displayed():
                            continue

                        tag = (el.tag_name or "").lower()
                        aria = (el.get_attribute("aria-label") or "").lower()
                        role = (el.get_attribute("role") or "").lower()
                        contenteditable = (el.get_attribute("contenteditable") or "").lower()

                        # accept textarea directly
                        if tag == "textarea":
                            print(f"✅ Caption box found using XPath: {xpath}")
                            print("Caption HTML:", el.get_attribute("outerHTML")[:500])
                            return el

                        # accept contenteditable or textbox
                        if contenteditable == "true" or role == "textbox":
                            print(f"✅ Caption box found using XPath: {xpath}")
                            print("Caption HTML:", el.get_attribute("outerHTML")[:500])
                            return el

                        # accept aria-label based caption fields
                        if "caption" in aria:
                            print(f"✅ Caption box found using XPath: {xpath}")
                            print("Caption HTML:", el.get_attribute("outerHTML")[:500])
                            return el

                    except Exception:
                        continue
            except Exception:
                continue

        # 2. JS fallback - dialog scoped first
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

                const dialogs = Array.from(document.querySelectorAll("div[role='dialog']"));
                const roots = dialogs.length ? dialogs : [document];

                for (const root of roots) {
                    const nodes = Array.from(
                        root.querySelectorAll("textarea, div[contenteditable='true'], div[role='textbox'], [aria-label], [placeholder]")
                    );

                    for (const node of nodes) {
                        if (!isVisible(node)) continue;

                        const aria = (node.getAttribute("aria-label") || "").toLowerCase();
                        const placeholder = (node.getAttribute("placeholder") || "").toLowerCase();
                        const role = (node.getAttribute("role") || "").toLowerCase();
                        const ce = (node.getAttribute("contenteditable") || "").toLowerCase();
                        const tag = (node.tagName || "").toLowerCase();

                        if (
                            tag === "textarea" ||
                            ce === "true" ||
                            role === "textbox" ||
                            aria.includes("caption") ||
                            placeholder.includes("caption")
                        ) {
                            return node;
                        }
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
                "return (document.body.innerText || '').slice(0, 2000);"
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