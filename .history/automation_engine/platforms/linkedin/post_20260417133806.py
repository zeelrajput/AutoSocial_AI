import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    POST_BUTTON_SELECTORS,
)


def close_linkedin_popups(driver):
    popup_xpaths = [
        "//button[@aria-label='Dismiss']",
        "//button[@aria-label='Close']",
        "//button[contains(@class,'artdeco-modal__dismiss')]",
        "//button[.//span[normalize-space()='Not now']]",
        "//button[.//span[normalize-space()='Got it']]",
        "//button[.//span[normalize-space()='Skip']]",
    ]

    for xpath in popup_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        print("Closed popup using:", xpath)
                except Exception:
                    continue
        except Exception:
            continue


def find_start_post_button(driver):
    # CSS selectors
    for selector in START_POST_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if not (el.is_displayed() and el.is_enabled()):
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
                        print("Start post button found using CSS:", selector)
                        print("Button text:", el.text)
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # XPath fallback
    xpath_candidates = [
        "//button[@aria-label='Start a post']",
        "//button[contains(@aria-label,'Start a post')]",
        "//div[@role='button' and @aria-label='Start a post']",
        "//div[@role='button' and contains(@aria-label,'Start a post')]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::button[1]",
        "//span[contains(normalize-space(),'Start a post')]/ancestor::*[@role='button'][1]",
        "//div[contains(normalize-space(),'Start a post') and @role='button']",
        "//button[contains(., 'Start a post')]",
        "//div[@role='button'][.//span[contains(., 'Start a post')]]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"Checking xpath: {xpath} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        print("Start post button found using XPath:", xpath)
                        print("Button text:", el.text)
                        print("Aria label:", el.get_attribute("aria-label"))
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    # JavaScript fallback
    try:
        js_element = driver.execute_script("""
            const candidates = Array.from(document.querySelectorAll('button, div[role="button"], a'));
            return candidates.find(el => {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();

                const visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                if (!visible) return false;

                return (
                    text.includes('start a post') ||
                    aria.includes('start a post') ||
                    cls.includes('share-box-feed-entry__trigger') ||
                    cls.includes('share-box-feed-entry--closed')
                );
            }) || null;
        """)
        if js_element:
            print("Start post button found using JavaScript fallback")
            return js_element
    except Exception as e:
        print("JavaScript fallback failed:", str(e))

    return None


def find_visible_dialogs(driver):
    dialogs = []

    css_candidates = [
        "div[role='dialog']",
        "div.artdeco-modal",
    ]

    for selector in css_candidates:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking dialog selector: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if el.is_displayed():
                        dialogs.append(el)
                except Exception:
                    continue
        except Exception:
            continue

    print("Visible dialogs count:", len(dialogs))
    return dialogs


def find_linkedin_textbox_in_container(container):
    css_candidates = [
        "div.ql-editor",
        "div[role='textbox']",
        "div[contenteditable='true']",
        "textarea",
        "p",
    ]

    for selector in css_candidates:
        try:
            elements = container.find_elements(By.CSS_SELECTOR, selector)
            print(f"Checking textbox selector inside dialog: {selector} -> found {len(elements)} elements")
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue

                    tag_name = (el.tag_name or "").lower()
                    contenteditable = (el.get_attribute("contenteditable") or "").strip().lower()
                    role = (el.get_attribute("role") or "").strip().lower()
                    cls = (el.get_attribute("class") or "").strip().lower()
                    placeholder = (el.get_attribute("data-placeholder") or "").strip().lower()
                    aria_label = (el.get_attribute("aria-label") or "").strip().lower()
                    text = (el.text or "").strip().lower()

                    if tag_name == "textarea":
                        print("Textbox found using textarea")
                        return el

                    if (
                        contenteditable == "true"
                        or role == "textbox"
                        or "ql-editor" in cls
                        or placeholder
                        or "textbox" in aria_label
                        or "editor" in aria_label
                    ):
                        print("Textbox found using dialog container selector:", selector)
                        return el

                    if tag_name in ["div", "p"] and ("write" in text or "share" in text or "talk about" in text):
                        print("Possible textbox-like element found:", selector)
                        return el
                except Exception:
                    continue
        except Exception:
            continue

    return None


def wait_for_linkedin_composer(driver, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        # 1. Dialog-based UI
        dialogs = find_visible_dialogs(driver)

        for idx, dialog in enumerate(dialogs, start=1):
            try:
                print(f"Checking visible dialog #{idx}")
                time.sleep(1)

                textbox = find_linkedin_textbox_in_container(dialog)
                if textbox:
                    print(f"LinkedIn composer detected in dialog #{idx}")
                    return dialog, textbox
            except Exception:
                continue

        # 2. Placeholder-based composer detection
        try:
            placeholder_xpaths = [
                "//*[contains(text(),'What do you want to talk about?')]",
                "//*[contains(text(),'what do you want to talk about?')]",
            ]

            for xpath in placeholder_xpaths:
                elements = driver.find_elements(By.XPATH, xpath)
                print(f"Checking placeholder xpath: {xpath} -> found {len(elements)} elements")

                for el in elements:
                    try:
                        if not el.is_displayed():
                            continue

                        # find clickable/editable parent
                        editor = driver.execute_script("""
                            let node = arguments[0];
                            while (node) {
                                const tag = (node.tagName || '').toLowerCase();
                                const role = (node.getAttribute && node.getAttribute('role') || '').toLowerCase();
                                const ce = (node.getAttribute && node.getAttribute('contenteditable') || '').toLowerCase();
                                const cls = (node.className || '').toString().toLowerCase();

                                if (
                                    ce === 'true' ||
                                    role === 'textbox' ||
                                    cls.includes('ql-editor') ||
                                    cls.includes('editor') ||
                                    tag === 'textarea'
                                ) {
                                    return node;
                                }

                                node = node.parentElement;
                            }
                            return arguments[0];
                        """, el)

                        if editor:
                            print("LinkedIn composer detected using placeholder text")
                            return None, editor
                    except Exception:
                        continue
        except Exception as e:
            print("Placeholder detection failed:", str(e))

        # 3. Broad global fallback
        try:
            global_editors = driver.find_elements(
                By.CSS_SELECTOR,
                "div[contenteditable='true'], div[role='textbox'], div.ql-editor, textarea, [data-placeholder]"
            )
            print("Checking global editors:", len(global_editors))

            for el in global_editors:
                try:
                    if not el.is_displayed():
                        continue

                    cls = (el.get_attribute("class") or "").lower()
                    role = (el.get_attribute("role") or "").lower()
                    contenteditable = (el.get_attribute("contenteditable") or "").lower()
                    placeholder = (el.get_attribute("data-placeholder") or "").lower()
                    aria = (el.get_attribute("aria-label") or "").lower()

                    if (
                        contenteditable == "true"
                        or role == "textbox"
                        or "ql-editor" in cls
                        or "editor" in cls
                        or placeholder
                        or "editor" in aria
                        or "textbox" in aria
                    ):
                        print("LinkedIn INLINE editor detected")
                        return None, el
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(0.5)

    return None, None


def type_into_linkedin_editor(driver, textbox, text):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textbox)
        time.sleep(1)

        try:
            safe_click(driver, textbox)
        except Exception:
            driver.execute_script("arguments[0].click();", textbox)

        time.sleep(1)

        try:
            driver.execute_script("arguments[0].focus();", textbox)
        except Exception:
            pass

        time.sleep(0.5)

        try:
            active = driver.switch_to.active_element
            if active and active.is_displayed():
                textbox = active
                print("Using active element as textbox")
        except Exception:
            pass

        # Clear content
        try:
            textbox.send_keys(Keys.CONTROL + "a")
            textbox.send_keys(Keys.DELETE)
            time.sleep(0.5)
        except Exception:
            pass

        # Normal typing
        try:
            for ch in text:
                textbox.send_keys(ch)
                time.sleep(0.03)
            print("Caption typed using send_keys")
            return True
        except Exception as e:
            print("send_keys failed:", str(e))

        # JS fallback
        try:
            driver.execute_script("""
                const el = arguments[0];
                const text = arguments[1];

                el.focus();

                if (document.activeElement !== el) {
                    el.click();
                    el.focus();
                }

                if ('value' in el) {
                    el.value = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return;
                }

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
                    data: text,
                    inputType: 'insertText'
                }));

                el.dispatchEvent(new KeyboardEvent('keyup', {
                    bubbles: true,
                    key: ' ',
                    code: 'Space'
                }));
            """, textbox, text)

            print("Caption typed using JS fallback")
            return True
        except Exception as e:
            print("JS typing failed:", str(e))

        return False

    except Exception as e:
        print("type_into_linkedin_editor error:", str(e))
        return False


def find_post_button(driver, dialog=None):
    search_root = dialog if dialog is not None else driver

    for selector in POST_BUTTON_SELECTORS:
        try:
            local_selector = selector.replace("div[role='dialog'] ", "")
            elements = search_root.find_elements(By.CSS_SELECTOR, local_selector)
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
        ".//button[contains(@class,'share-actions__primary-action')]",
        ".//button[@aria-label='Post']",
        ".//button[contains(@aria-label,'Post')]",
        ".//span[normalize-space()='Post']/ancestor::button[1]",
        "//button[contains(., 'Post')]",
    ]

    for xpath in xpath_candidates:
        try:
            elements = search_root.find_elements(By.XPATH, xpath)
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
        time.sleep(10)
        medium_pause()

        try:
            driver.refresh()
            print("LinkedIn feed page refreshed")
            time.sleep(6)
        except Exception:
            pass

        medium_pause()

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        try:
            body_preview = driver.execute_script("return document.body.innerText.slice(0, 2000);")
            print("Page text preview:", body_preview)
        except Exception:
            pass

        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception:
            pass

        close_linkedin_popups(driver)

        start_post_button = find_start_post_button(driver)
        if not start_post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_not_found")
            return {
                "success": False,
                "message": f"Start post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                start_post_button
            )
            time.sleep(1)

            clicked = safe_click(driver, start_post_button)
            if not clicked:
                try:
                    start_post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", start_post_button)
                    print("Start post clicked using JavaScript fallback")

            print("LinkedIn 'Start a post' trigger clicked")
        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_start_post_click_failed")
            return {
                "success": False,
                "message": f"Start post click failed: {str(e)}. Screenshot: {screenshot}"
            }

        time.sleep(2)

        for i in range(5):
            print(f"Waiting for editor render... {i + 1}")
            time.sleep(1)

        print("After click URL:", driver.current_url)
        print("After click title:", driver.title)

        dialog, textbox = wait_for_linkedin_composer(driver, timeout=12)

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_composer_not_opened")
            return {
                "success": False,
                "message": f"LinkedIn composer opened visually but textbox was not detected. Screenshot: {screenshot}"
            }

        try:
            outer_html = driver.execute_script("return arguments[0].outerHTML;", textbox)
            print("Textbox outerHTML:", outer_html[:1000] if outer_html else "None")
        except Exception:
            pass

        typed = type_into_linkedin_editor(driver, textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, prefix="linkedin_typing_failed")
            return {
                "success": False,
                "message": f"Typing failed. Screenshot: {screenshot}"
            }

        time.sleep(2)
        medium_pause()

        post_button = find_post_button(driver, dialog=dialog if dialog else driver)
        if not post_button:
            post_button = find_post_button(driver)

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                post_button
            )
            time.sleep(1)

            clicked = safe_click(driver, post_button)
            if not clicked:
                try:
                    post_button.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", post_button)
                    print("Post button clicked using JavaScript")

            print("Post published on LinkedIn")
            medium_pause()

            return {
                "success": True,
                "message": "Post published on LinkedIn"
            }

        except Exception as e:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"LinkedIn post button click failed: {str(e)}. Screenshot: {screenshot}"
            }

    except Exception as e:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        screenshot = save_screenshot(driver, prefix="linkedin_post_error")
        return {
            "success": False,
            "message": f"{str(e)} | Screenshot: {screenshot}"
        }