import io
import os
import time

from PIL import Image
import win32clipboard
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from automation_engine.common.click_helper import safe_click
from automation_engine.common.type_helper import type_like_human
from .utils import (
    wait_for_linkedin_login,
    close_common_popups,
    find_start_post_button,
    find_linkedin_textbox,
    find_post_button,
    find_image_input,
    find_photo_button,
)


def wait_for_composer_open(driver, timeout=10):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            opened = driver.execute_script("""
                function isVisible(el) {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    return (
                        r.width > 10 &&
                        r.height > 10 &&
                        s.display !== 'none' &&
                        s.visibility !== 'hidden' &&
                        s.opacity !== '0'
                    );
                }

                const selectors = [
                    "div[role='dialog']",
                    "[aria-label*='Start a post']",
                    "[data-placeholder]",
                    "div[contenteditable='true']",
                    "div[role='textbox']",
                    ".ql-editor"
                ];

                for (const sel of selectors) {
                    const nodes = Array.from(document.querySelectorAll(sel));
                    for (const el of nodes) {
                        if (!isVisible(el)) continue;

                        const text = (
                            (el.innerText || '') + ' ' +
                            (el.textContent || '') + ' ' +
                            (el.getAttribute('aria-label') || '') + ' ' +
                            (el.getAttribute('data-placeholder') || '')
                        ).toLowerCase();

                        if (
                            text.includes('what do you want to talk about') ||
                            text.includes('post to anyone