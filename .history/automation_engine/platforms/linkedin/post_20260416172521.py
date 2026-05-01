import time
from selenium.webdriver.common.by import By

from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def find_start_post_button(driver):
    # 1) Strict CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    href = (el.get_attribute("href") or "").strip().lower()
                    if "/in/" in href:
                        continue

                    aria = (el.get_attribute("aria-label") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()
                    text = (el.text or "").strip().lower()

                    if (
                        "start a post" in aria
                        or "start a post" in text
                        or "share-box-feed-entry__trigger" in cls
                        or "share-box-feed-entry--closed" in cls
                    ):
                        print("Start post button found using CSS:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # 2) XPath candidates
    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and @aria-label='Start a post']",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//button[contains(@class,'share-box-feed-entry__trigger')]",
        "//div[contains(@class,'share-box-feed-entry__trigger')]",
        "//div[contains(@class,'share-box-feed-entry--closed')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    href = (el.get_attribute("href") or "").strip().lower()
                    if "/in/" in href:
                        continue

                    text = (el.text or "").strip().lower()
                    aria = (el.get_attribute("aria-label") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()

                    if (
                        "start a post" in text
                        or "start a post" in aria
                        or "share-box-feed-entry__trigger" in cls
                        or "share-box-feed-entry--closed" in cls
                    ):
                        print("Start post button found using XPath:", xpath)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # 3) JavaScript fallback — safest last resort
    try:
        element = driver.execute_script("""
            const nodes = Array.from(document.querySelectorAll('button, div[role="button"], div, span'));
            for (const el of nodes) {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();
                const href = (el.getAttribute('href') || '').trim().toLowerCase();

                if (href.includes('/in/')) continue;

                if (
                    aria.includes('start a post') ||
                    text === 'start a post' ||
                    cls.includes('share-box-feed-entry__trigger') ||
                    cls.includes('share-box-feed-entry--closed')
                ) {
                    return el;
                }
            }
            return null;
        """)
        if element:
            print("Start post button found using JavaScript fallback")
            return element
    except Exception as e:
        print("Start post JS fallback failed:", str(e))

    return None

def wait_for_popup(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        xpath_candidates = [
            "//*[contains(normalize-space(), 'What do you want to talk about?')]",
            "//div[contains(@class,'ql-editor')]",
            "//div[@contenteditable='true']",
            "//div[@role='textbox']",
        ]

        for xpath in xpath_candidates:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        if el.is_displayed():
                            print("Popup/editor visible using:", xpath)
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        time.sleep(0.5)

    return False


def get_real_editor(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        # Most important: LinkedIn real editor first
        selectors = [
            "div.ql-editor[contenteditable='true']",
            "div[role='textbox'][contenteditable='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ]

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    try:
                        if not el.is_displayed():
                            continue

                        cls = (el.get_attribute("class") or "").lower()
                        contenteditable = (el.get_attribute("contenteditable") or "").lower()

                        if contenteditable == "true":
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                            except Exception:
                                pass

                            try:
                                safe_click(driver, el)
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", el)
                                except Exception:
                                    pass

                            try:
                                driver.execute_script("arguments[0].focus();", el)
                            except Exception:
                                pass

                            time.sleep(1)
                            print("Real editor found using:", selector, "| class:", cls)
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # fallback: click placeholder text area first, then retry
        try:
            placeholders = driver.find_elements(
                By.XPATH,
                "//*[contains(normalize-space(), 'What do you want to talk about?')]"
            )
            for ph in placeholders:
                try:
                    if ph.is_displayed():
                        safe_click(driver, ph)
                        print("Clicked placeholder area")
                        time.sleep(1)
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(0.5)

    return None

def type_in_editor(driver, textbox, text):
    try:
        textbox.click()
    except Exception:
        pass

    try:
        driver.execute_script("arguments[0].focus();", textbox)
    except Exception:
        pass

    try:
        type_like_human(textbox, text)
        print("Caption typed using type_like_human")
        return True
    except Exception:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();

            if (el.innerHTML !== undefined) {
                el.innerHTML = '';
                el.textContent = text;
                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    data: text,
                    inputType: 'insertText'
                }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                el.value = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        """, textbox, text)
        print("Caption typed using JavaScript fallback")
        return True
    except Exception:
        return False


def find_post_button(driver):
    for selector in POST_BUTTON_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        print("Post button found using CSS:", selector)
                        return btn
                except Exception:
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
                        print("Post button found using XPath:", xpath)
                        return btn
                except Exception:
                    continue
        except Exception:
            continue

    return None


def post_to_linkedin(driver, post):
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)
        medium_pause()

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_post_button)
            time.sleep(1)

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Start post clicked using JavaScript")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        popup_open = wait_for_popup(driver, timeout=6)
        if not popup_open:
            try:
                driver.execute_script("arguments[0].click();", start_post_button)
                print("Retried Start post with JavaScript click")
            except Exception:
                pass

            popup_open = wait_for_popup(driver, timeout=6)

        if not popup_open:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer did not open. Screenshot: {screenshot}"
            }

        textbox = get_real_editor(driver, timeout=10)
        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        typed = type_in_editor(driver, textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"LinkedIn text could not be written. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        post_button = find_post_button(driver)
        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        clicked = safe_click(driver, post_button)
        if not clicked:
            try:
                driver.execute_script("arguments[0].click();", post_button)
                print("Post button clicked using JavaScript")
            except Exception:
                screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
                return {
                    "success": False,
                    "message": f"LinkedIn post button click failed. Screenshot: {screenshot}"
                }

        print("Post published on LinkedIn")
        medium_pause()

        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}