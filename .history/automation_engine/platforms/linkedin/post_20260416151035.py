# post.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selectors import START_POST_SELECTORS, TEXTBOX_SELECTORS, POST_BUTTON_SELECTORS

def find_element(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except:
            continue
    return None


def click_element(driver, selectors, timeout=10):
    for selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except:
            continue
    return False


def post_on_linkedin(driver, caption):
    try:
        print("Opening LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        # 1. Click Start Post
        print("Finding 'Start a post' button...")
        if not click_element(driver, START_POST_SELECTORS):
            print("Failed to click Start Post")
            return {"success": False, "message": "Start post button not found"}

        print("Clicked Start Post")
        time.sleep(3)

        # 2. Find Textbox
        print("Finding textbox...")
        textbox = find_element(driver, TEXTBOX_SELECTORS)

        if not textbox:
            print("Textbox not found")
            return {"success": False, "message": "Textbox not found"}

        textbox.click()
        time.sleep(1)

        print("Typing caption...")
        textbox.send_keys(caption)
        time.sleep(2)

        # 3. Click Post Button
        print("Clicking Post button...")
        if not click_element(driver, POST_BUTTON_SELECTORS):
            print("Post button not found")
            return {"success": False, "message": "Post button not found"}

        print("Post successful!")
        return {"success": True, "message": "Posted successfully"}

    except Exception as e:
        return {"success": False, "message": str(e)}