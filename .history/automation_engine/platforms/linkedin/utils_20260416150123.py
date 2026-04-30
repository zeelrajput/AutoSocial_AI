# automation_engine/platforms/linkedin/utils.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def is_logged_in(driver) -> bool:
    """
    Check if the user is already logged into LinkedIn.
    Returns True if the feed page loads with the main nav present.
    """
    try:
        driver.get("https://www.linkedin.com/feed/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav.global-nav"))
        )
        return True
    except Exception:
        return False


def scroll_to_top(driver) -> None:
    """
    Scroll the page back to the top (needed before finding the Start a Post button).
    """
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except Exception:
        pass


def dismiss_any_overlay(driver) -> None:
    """
    Dismiss any overlay, tooltip, or cookie banner that might block interactions.
    """
    dismiss_selectors = [
        "button[aria-label='Dismiss']",
        "button[data-tracking-control-name='overlay-cta-dismiss']",
        ".artdeco-toast-item__dismiss",
    ]
    for selector in dismiss_selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, selector)
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
        except Exception:
            continue


def wait_for_feed(driver, timeout: int = 20) -> bool:
    """
    Wait until the LinkedIn feed (main content) is loaded.
    Returns True if loaded, False on timeout.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        return True
    except Exception:
        return False


def get_current_url(driver) -> str:
    """
    Safely return the driver's current URL.
    """
    try:
        return driver.current_url
    except Exception:
        return ""