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
            detach: bool = True,
            headless: bool = False
    ) -> None:
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        self.detach = detach
        self.headless = headless

    def _validate_profile_path(self) -> None:
        """
        validate the chrome user data directory if provided
        """

        if self.user_data_dir:
            profile_root = pa