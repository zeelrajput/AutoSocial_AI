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
            profile_root = Path(self.user_data_dir)
            if not profile_root.exists():
                return FileNotFoundError(f"chrome user data directory not found: {self.user_data_dir}")
            
    def _build_options(self) -> Options:
        """
        build chrome options
        """

        # basic browser behavior
        Options.add_argument("--start-maximized")
        Options.add_argument("--disable-notifications")
        Options.add_argument("--disable-popup_blocking")
        Options.add_argument("--no-default-browser-check")

        # keep browser open after script ends
        Options.add_experimental_option("detach", self.detach)

        # use user's existing chrome profile/session
        if self.user_data_dir:
            