import time
from selenium.webdriver.common.by import By

from automation_engine.common.wait_helper import wait_for_visible, wait_for_clickable
from automation_engine.common.type_helper import type_like_human
from automation_engine.common.click_helper import safe_click
from automation_engine.common.screenshot_helper import save_screenshot
from automation_engine.common.human_behavior import medium_pause
from automation_engine.platforms.linkedin.selectors import (
    START_POST_SELECTORS,
    TEXTBOX_SELECTORS,
    POST_BUTTON_SELECTORS,
)

def _find_first_visible(driver, selectors, timeout)