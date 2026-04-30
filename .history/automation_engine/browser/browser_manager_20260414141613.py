import os
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

class BrwoserManager:
    """
    starts and closes chrome for local selenium automation.

    This is designed for:
    - user-device-based execution
    - existing chrome login session reuse
    - socical media automation workflows
    """

    def __init__(
            self,
            user_data_dir: Options[str] = None,
            profile_directory: str = "Default",
            detach:
    ):