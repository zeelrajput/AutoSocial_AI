import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    PROFILE_URL,
    ACTIVITY_SECTION_XPATHS,
    CREATE_POST_BUTTON_XPATHS,
    TEXTBOX_XPATHS,
    POST_BUTTON_XPATHS,
)


def short_pause(seconds=1.0):
    time.sleep(seconds)


def is_visible(driver, element):
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
        """, element)
    except Exception:
        return False


def is_enabled(driver, element):
    try:
        return driver.execute_script("""
            const el = arguments[0];
            if (!el) return false;
            const ariaDisabled = el.getAttribute('aria-disabled');
            return !el.disabled && ariaDisabled !== 'true';
        """, element)
    except Exception:
        return False


def get_outer_html(driver, element, limit=1200):
    try:
        html = driver.execute_script(
            "return arguments[0] && arguments[0].outerHTML ? arguments[0].outerHTML : '';",
            element
        )
        return html[:limit]
    except Exception:
        return ""


def scroll_to_element(driver, element):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});",
            element
        )
        short_pause(1)
    except Exception:
        pass


def robust_click(driver, element, label="element"):
    methods = [
        ("safe_click", lambda: safe_click(driver, element)),
        ("selenium_click", lambda: element.click() or True),
        ("js_click", lambda: driver.execute_script("arguments[0].click();", element) or True),
        ("actionchains_click", lambda: ActionChains(driver).move_to_element(element).pause(0.4).click().perform() or True),
    ]

    for method_name, method in methods:
        try:
            scroll_to_element(driver, element)
            result = method()
            print(f"✅ {label} clicked using {method_name}")
            if result is False:
                continue
            return True
        except Exception as e:
            print(f"⚠️ {label} click failed using {method_name}: {e}")

    return False


def find_first_visible_by_xpaths(driver, xpaths, label="element", root=None, must_be_enabled=False):
    search_root = root if root is not None else driver

    for xpath in xpaths:
        try:
            elements = search_root.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed() or not is_visible(driver, el):
                        continue

                    if must_be_enabled and not is_enabled(driver, el):
                        continue

                    print(f"✅ {label} found using XPath: {xpath}")
                    return el
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    return None


def open_profile_page(driver):
    driver.get(PROFILE_URL)
    time.sleep(6)
    medium_pause()
    print("Current URL:", driver.current_url)
    print("Page title:", driver.title)


def find_activity_section(driver, max_scrolls=8):
    for i in range(max_scrolls):
        section = find_first_visible_by_xpaths(
            driver,
            ACTIVITY_SECTION_XPATHS,
            label="Activity section"
        )
        if section:
            scroll_to_element(driver, section)
            return section

        driver.execute_script("window.scrollBy(0, 700);")
        short_pause(1.5)
        print(f"🔄 Scrolling to find Activity section... attempt {i + 1}")

    return None


def click_create_post_from_activity(driver, activity_section):
    create_post_btn = find_first_visible_by_xpaths(
        driver,
        CREATE_POST_BUTTON_XPATHS,
        label="Create a post button",
        root=activity_section
    )

    if not create_post_btn:
        return False

    print("Create Post HTML:", get_outer_html(driver, create_post_btn))
    return robust_click(driver, create_post_btn, label="Create a post button")


def wait_for_share_surface(driver, timeout=12):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            current_url = driver.current_url.lower()
            page_html = driver.page_source.lower()

            if "/preload/sharebox" in current_url:
                print("✅ Sharebox URL detected:", driver.current_url)
                return True

            if "what do you want to talk about" in page_html:
                print("✅ Share composer text detected in page source")
                return True

            found = driver.execute_script("""
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 50 &&
                        r.height > 50 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                };

                const candidates = [
                    ...document.querySelectorAll("div[role='dialog']"),
                    ...document.querySelectorAll("div.artdeco-modal"),
                    ...document.querySelectorAll("main"),
                    ...document.querySelectorAll("form"),
                    ...document.querySelectorAll("section")
                ].filter(visible);

                return candidates.length > 0;
            """)
            if found:
                print("✅ Share surface detected")
                return True
        except Exception as e:
            print("⚠️ wait_for_share_surface error:", e)

        time.sleep(1)

    return False


def find_real_textbox(driver):
    candidates = []

    for xpath in TEXTBOX_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if not el.is_displayed() or not is_visible(driver, el):
                        continue

                    hint = (
                        (el.get_attribute("aria-label") or "") + " " +
                        (el.get_attribute("placeholder") or "") + " " +
                        (el.get_attribute("class") or "")
                    ).lower()

                    if any(x in hint for x in ["search", "message", "comment", "chat"]):
                        continue

                    score = 0

                    if el.get_attribute("contenteditable") == "true":
                        score += 5
                    if (el.get_attribute("role") or "").lower() == "textbox":
                        score += 4
                    if "ql-editor" in hint:
                        score += 5
                    if "editor" in hint:
                        score += 2
                    if "share" in hint:
                        score += 2

                    try:
                        parent_html = driver.execute_script("""
                            const el = arguments[0];
                            const p = el.closest("div[role='dialog'], div.artdeco-modal, form, section, main");
                            return p ? p.outerHTML.slice(0, 2000).toLowerCase() : '';
                        """, el)

                        if "what do you want to talk about" in parent_html:
                            score += 8
                        if "post to anyone" in parent_html:
                            score += 8
                        if "create a post" in parent_html:
                            score += 5
                    except Exception:
                        pass

                    candidates.append((score, xpath, el))
                except StaleElementReferenceException:
                    continue
        except Exception:
            continue

    if not candidates:
        print("⚠️ No textbox candidates found")
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_xpath, best_el = candidates[0]

    scroll_to_element(driver, best_el)

    try:
        driver.execute_script("arguments[0].focus();", best_el)
        best_el.click()
        time.sleep(1)
    except Exception:
        pass

    print(f"✅ Textbox found using XPath: {best_xpath}")
    print("⭐ Textbox score:", best_score)
    print("Focused textbox HTML:", get_outer_html(driver, best_el))
    return best_el


def type_into_element(driver, element, caption):
    targets = [element]

    try:
        active = driver.switch_to.active_element
        if active and active != element:
            targets.append(active)
    except Exception:
        pass

    for target in targets:
        try:
            driver.execute_script("arguments[0].focus();", target)
            time.sleep(0.5)
        except Exception:
            pass

        try:
            target.click()
        except Exception:
            pass

        try:
            target.send_keys(Keys.CONTROL, "a")
            target.send_keys(Keys.DELETE)
        except Exception:
            pass

        methods = [
            ("send_keys", lambda: target.send_keys(caption) or True),
            ("actionchains", lambda: ActionChains(driver).move_to_element(target).click().pause(0.4).send_keys(caption).perform() or True),
            (
                "js_fallback",
                lambda: driver.execute_script("""
                    const el = arguments[0];
                    const text = arguments[1];

                    el.focus();

                    if (el.tagName === 'TEXTAREA' || 'value' in el) {
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
                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: ' ' }));
                    return true;
                """, target, caption)
            )
        ]

        for method_name, method in methods:
            try:
                method()
                print(f"✅ Caption typed using {method_name}")
                time.sleep(1)

                typed_text = driver.execute_script("""
                    const el = arguments[0];
                    return (el.innerText || el.textContent || el.value || '').trim();
                """, target)

                print("📝 Text inside editor:", typed_text[:300])

                if typed_text.strip():
                    return True
            except Exception as e:
                print(f"⚠️ Typing failed using {method_name}: {e}")

    return False


def find_post_button(driver):
    try:
        btn = driver.execute_script("""
            const visible = (el) => {
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
            };

            const enabled = (el) => {
                if (!el) return false;
                return !el.disabled && el.getAttribute('aria-disabled') !== 'true';
            };

            const dialogs = [...document.querySelectorAll("div[role='dialog']")]
                .filter(visible);

            if (!dialogs.length) return null;

            const dialog = dialogs[dialogs.length - 1];

            const buttons = [...dialog.querySelectorAll("button")].filter(b => {
                const text = ((b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '')).trim().toLowerCase();
                return visible(b) && enabled(b) && text === 'post';
            });

            if (!buttons.length) return null;

            buttons.sort((a, b) => {
                const ar = a.getBoundingClientRect();
                const br = b.getBoundingClientRect();

                // prefer lower button, then right-most button
                if (br.top !== ar.top) return br.top - ar.top;
                return br.left - ar.left;
            });

            return buttons[0];
        """)
        if btn:
            print("✅ Post button found inside active dialog using JS")
            return btn
    except Exception as e:
        print("⚠️ JS dialog Post button search failed:", e)

    return None


def wait_until_post_button_enabled(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            btn = find_post_button(driver)
            if btn:
                print("✅ Post button is enabled")
                print("Post button HTML:", get_outer_html(driver, btn))
                return btn
        except Exception as e:
            print("⚠️ Waiting for Post button failed:", e)

        time.sleep(1)

    return None

def verify_post_success(driver, timeout=15):
    end_time = time.time() + timeout

    while time.time() < end_time:
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

                if (successMarkers.some(x => bodyText.includes(x))) {
                    return true;
                }

                const visibleDialogs = Array.from(document.querySelectorAll("div[role='dialog'], div.artdeco-modal"))
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

                if (visibleDialogs.length === 0) {
                    return true;
                }

                return false;
            """)
            if confirmed:
                return True
        except Exception:
            pass

        short_pause(1)

    return False


def post_to_linkedin(driver, post):
    try:
        caption = str(post.caption).strip()

        open_profile_page(driver)

        activity_section = find_activity_section(driver)
        if not activity_section:
            screenshot = save_screenshot(driver, prefix="linkedin_activity_section_not_found")
            return {
                "success": False,
                "message": f"Activity section not found. Screenshot: {screenshot}"
            }

        print("Activity HTML:", get_outer_html(driver, activity_section))

        clicked = click_create_post_from_activity(driver, activity_section)
        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_create_post_click_failed")
            return {
                "success": False,
                "message": f"Create a post button click failed. Screenshot: {screenshot}"
            }

        short_pause(2)

        opened = wait_for_share_surface(driver, timeout=12)
        if not opened:
            print("⚠️ Share surface detection failed, opening sharebox directly...")
            try:
                driver.get("https://www.linkedin.com/preload/sharebox/")
                time.sleep(4)
                opened = wait_for_share_surface(driver, timeout=8)
            except Exception as e:
                print("⚠️ Direct sharebox fallback failed:", e)

        time.sleep(2)
        textbox = find_real_textbox(driver)

        if not textbox:
            try:
                active = driver.switch_to.active_element
                if active and active.tag_name:
                    print("✅ Using active element as fallback:", active.tag_name)
                    textbox = active
            except Exception as e:
                print("⚠️ Active element fallback failed:", str(e))

        if not textbox:
            screenshot = save_screenshot(driver, prefix="linkedin_textbox_not_found")
            return {
                "success": False,
                "message": f"LinkedIn textbox not found. Screenshot: {screenshot}"
            }

        typed = type_into_element(driver, textbox, caption)
        if not typed:
            try:
                ActionChains(driver).send_keys(Keys.TAB).perform()
                short_pause(1)
                textbox = find_real_textbox(driver) or textbox
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

        post_button = wait_until_post_button_enabled(driver, timeout=10)

        if not post_button:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_not_found")
            return {
                "success": False,
                "message": f"LinkedIn post button not found. Screenshot: {screenshot}"
            }

        print("Post button HTML:", get_outer_html(driver, post_button))

        clicked = robust_click(driver, post_button, label="Post button")
        if not clicked:
            screenshot = save_screenshot(driver, prefix="linkedin_post_button_click_failed")
            return {
                "success": False,
                "message": f"LinkedIn post button click failed. Screenshot: {screenshot}"
            }

        print("✅ Post button clicked")
        short_pause(6)

        confirmed = verify_post_success(driver, timeout=15)
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