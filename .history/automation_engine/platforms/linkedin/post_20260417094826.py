import time
import random
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation_engine.common.screenshot_helper import save_screenshot


# -------------------- LOGGING --------------------
logging.basicConfig(
    filename="linkedin_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------- HUMAN BEHAVIOR --------------------
def human_pause(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


# -------------------- RETRY SYSTEM --------------------
def retry(action_fn, attempts=3, delay=2, name="action"):
    for attempt in range(attempts):
        try:
            result = action_fn()
            if result:
                return result
        except Exception as e:
            logging.error(f"{name} failed (attempt {attempt+1}): {e}")

        time.sleep(delay)

    return None


# -------------------- WAIT HELPERS --------------------
def wait_for_feed(driver):
    WebDriverWait(driver, 25).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'share-box-feed-entry')]")
        )
    )

def wait_for_modal(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
        )
        return True
    except:
        return False


# -------------------- STATE CHECK --------------------
def is_composer_open(driver):
    try:
        modal = driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
        textbox = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
        return modal.is_displayed() and textbox.is_displayed()
    except:
        return False


# -------------------- CLICK --------------------
def human_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        human_pause(0.5, 1.5)

        ActionChains(driver).move_to_element(element).pause(0.5).click().perform()
        return True
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False


# -------------------- FIND ELEMENTS --------------------
def find_start_post_button(driver):
    selectors = [
        "button[aria-label='Start a post']",
        "button[aria-label*='Start a post']",
        "div[role='button'][aria-label*='Start a post']",
        ".share-box-feed-entry__trigger"
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if el.is_displayed() and el.is_enabled():
                    return el
        except:
            continue

    return None


def find_textbox(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
        for el in elements:
            if el.is_displayed():
                return el
    except:
        pass

    return None


def find_post_button(driver):
    selectors = [
        "button.share-actions__primary-action",
        "button[aria-label='Post']",
        "button[aria-label*='Post']"
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in elements:
                if btn.is_displayed() and btn.is_enabled():
                    return btn
        except:
            continue

    return None


# -------------------- MAIN ACTIONS --------------------
def open_composer(driver, start_btn):

    def attempt():
        logging.info("Trying to open composer")

        human_click(driver, start_btn)
        time.sleep(2)

        return is_composer_open(driver)

    return retry(attempt, attempts=3, delay=3, name="Open Composer")


def type_post(textbox, text):
    try:
        textbox.click()
        human_pause(1, 2)

        for char in text:
            textbox.send_keys(char)
            time.sleep(0.02)

        return True
    except Exception as e:
        logging.error(f"Typing failed: {e}")
        return False


def click_post(driver):

    def attempt():
        btn = find_post_button(driver)
        if not btn:
            return False

        return human_click(driver, btn)

    return retry(attempt, attempts=3, name="Click Post")


# -------------------- MAIN FUNCTION --------------------
def post_to_linkedin(driver, post):
    try:
        logging.info("Starting LinkedIn post")

        driver.get("https://www.linkedin.com/feed/")
        wait_for_page_load(driver)
        human_pause(3, 5)

        start_btn = find_start_post_button(driver)
        if not start_btn:
            screenshot = save_screenshot(driver, "start_btn_not_found")
            return {"success": False, "message": f"Start button not found: {screenshot}"}

        opened = open_composer(driver, start_btn)
        if not opened:
            screenshot = save_screenshot(driver, "composer_not_opened")
            return {"success": False, "message": f"Composer not opened: {screenshot}"}

        wait_for_modal(driver)

        textbox = find_textbox(driver)
        if not textbox:
            screenshot = save_screenshot(driver, "textbox_not_found")
            return {"success": False, "message": f"Textbox not found: {screenshot}"}

        typed = type_post(textbox, post.caption)
        if not typed:
            screenshot = save_screenshot(driver, "typing_failed")
            return {"success": False, "message": f"Typing failed: {screenshot}"}

        human_pause(2, 4)

        posted = click_post(driver)
        if not posted:
            screenshot = save_screenshot(driver, "post_failed")
            return {"success": False, "message": f"Post click failed: {screenshot}"}

        logging.info("Post published successfully")
        return {"success": True, "message": "Post published on LinkedIn"}

    except Exception as e:
        screenshot = save_screenshot(driver, "fatal_error")
        logging.error(f"Fatal error: {e}")
        return {"success": False, "message": f"{str(e)} | Screenshot: {screenshot}"}