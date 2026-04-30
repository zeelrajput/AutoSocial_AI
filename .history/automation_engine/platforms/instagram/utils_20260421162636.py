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