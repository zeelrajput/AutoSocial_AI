import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def find_start_post_button(driver):
    # 1) CSS selectors
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

    # 2) XPath selectors
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

                    print("Start post button found using XPath:", xpath)
                    return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def get_real_editor(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
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

                        contenteditable = (el.get_attribute("contenteditable") or "").lower()
                        if contenteditable != "true":
                            continue

                        try:
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", el
                            )
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
                        print("Real editor found using:", selector)
                        return el
                    except Exception:
                        continue
            except Exception:
                continue

        # click placeholder if visible
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
        safe_click(driver, textbox)
    except Exception:
        pass

    try:
        driver.execute_script("arguments[0].focus();", textbox)
    except Exception:
        pass

    time.sleep(1)

    # 1. direct send_keys
    try:
        textbox.send_keys(text)
        print("Caption typed using textbox.send_keys")
        return True
    except Exception:
        pass

    # 2. ActionChains
    try:
        ActionChains(driver).move_to_element(textbox).click().send_keys(text).perform()
        print("Caption typed using ActionChains")
        return True
    except Exception:
        pass

    # 3. helper typing
    try:
        type_like_human(textbox, text)
        print("Caption typed using type_like_human")
        return True
    except Exception:
        pass

    # 4. JS fallback
    try:
        driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            el.focus();

            if (el.getAttribute('contenteditable') === 'true') {
                el.innerHTML = '';
                el.textContent = text;

                el.dispatchEvent(new InputEvent('beforeinput', {
                    bubbles: true,
                    cancelable: true,
                    inputType: 'insertText',
                    data: text
                }));

                el.dispatchEvent(new InputEvent('input', {
                    bubbles: true,
                    inputType: 'insertText',
                    data: text
                }));

                el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'a' }));
                el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'a' }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            } else {
                el.value = text;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        """, textbox, text)
        print("Caption typed using JavaScript fallback")
        return True
    except Exception as e:
        print("Typing failed:", str(e))
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
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                start_post_button
            )
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

        time.sleep(3)
        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        if "/in/" in driver.current_url:
            screenshot = save_screenshot(driver, prefix="linkedin_wrong_click")
            return {
                "success": False,
                "message": f"Wrong Start Post element clicked. Screenshot: {screenshot}"
            }

        # Click placeholder first if visible
        try:
            placeholders = driver.find_elements(
                By.XPATH,
                "//*[contains(normalize-space(), 'What do you want to talk about?')]"
            )
            for ph in placeholders:
                try:
                    if ph.is_displayed():
                        safe_click(driver, ph)
                        print("Clicked placeholder before finding editor")
                        time.sleep(1)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        textbox = get_real_editor(driver, timeout=12)
        print("Textbox outerHTML:", textbox.get_attribute("outerHTML")[:1000] if textbox else "None")

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