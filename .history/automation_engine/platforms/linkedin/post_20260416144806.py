import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from au
# Import selectors
# from selectors import COMPOSE_SELECTORS, TEXTBOX_SELECTORS, POST_BUTTON_SELECTORS


def human_delay(min_sec=0.5, max_sec=1.5):
    import random
    time.sleep(random.uniform(min_sec, max_sec))


def find_element_with_fallback(driver, selectors, by=By.CSS_SELECTOR, timeout=10):
    wait = WebDriverWait(driver, timeout)

    for selector in selectors:
        try:
            if selector.startswith("//"):  # XPath
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            else:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return element
        except:
            continue

    return None


def click_start_post(driver):
    print("🔍 Finding 'Start a post' button...")

    btn = find_element_with_fallback(driver, COMPOSE_SELECTORS)

    if not btn:
        raise Exception("❌ Start post button not found")

    driver.execute_script("arguments[0].click();", btn)
    print("✅ Clicked 'Start a post'")
    human_delay(2, 3)


def write_post(driver, text):
    print("✍️ Writing post...")

    textbox = find_element_with_fallback(driver, TEXTBOX_SELECTORS)

    if not textbox:
        raise Exception("❌ Textbox not found")

    textbox.click()
    human_delay()

    for char in text:
        textbox.send_keys(char)
        time.sleep(0.02)  # typing delay

    print("✅ Text entered")
    human_delay(1, 2)


def click_post_button(driver):
    print("🚀 Clicking post button...")

    btn = find_element_with_fallback(driver, POST_BUTTON_SELECTORS)

    if not btn:
        raise Exception("❌ Post button not found")

    driver.execute_script("arguments[0].click();", btn)
    print("✅ Post submitted")


def post_on_linkedin(driver, text):
    try:
        print("🌐 Opening LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)

        click_start_post(driver)
        write_post(driver, text)
        click_post_button(driver)

        print("🎉 LinkedIn post successful")

    except Exception as e:
        print("❌ Error:", str(e))