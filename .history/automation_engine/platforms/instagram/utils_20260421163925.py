import time
from selenium.webdriver.common.by import By

from .selectors import (
    CREATE_BUTTON_XPATHS,
    NEXT_BUTTON_XPATHS,
    CAPTION_XPATHS,
    SHARE_BUTTON_XPATHS,
)

def find_create_button(driver):
    for xpath in CREATE_BUTTON_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except:
            continue
    return None


def click_next(driver):
    for _ in range(5):
        for xpath in NEXT_BUTTON_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        el.click()
                        time.sleep(2)
                        print("✅ Next clicked")
                        return True
            except:
                continue
        time.sleep(1)
    return False


def find_caption_box(driver):
    for xpath in CAPTION_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except:
            continue
    return None


def find_share_button(driver):
    for _ in range(5):
        for xpath in SHARE_BUTTON_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        return el
            except:
                continue
        time.sleep(1)
    return None

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

            # ✅ Logged in if login page gone
            if "accounts/login" not in current_url:
                if "instagram.com" in current_url:
                    print("✅ Instagram login detected")
                    return True

            # ⏳ Handle OTP / challenge
            if (
                "challenge" in current_url or
                "two-factor" in current_url or
                "security code" in body_text
            ):
                print("⏳ Waiting for verification...")

        except Exception as e:
            print("⚠️ Login detection error:", str(e))

        time.sleep(2)

    print("❌ Login timeout")
    return False

import time
from selenium.webdriver.common.by import By

from .selectors import FILE_INPUT_XPATHS, SELECT_FROM_COMPUTER_XPATHS


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


def find_file_input(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        for xpath in FILE_INPUT_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    try:
                        return el
                    except Exception:
                        continue
            except Exception:
                continue
        time.sleep(1)

    return None

def find_new_post_button(driver):
    from .selectors import NEW_POST_XPATHS
    from selenium.webdriver.common.by import By

    for xpath in NEW_POST_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                if el.is_displayed():
                    return el
        except Exception:
            continue
    return None