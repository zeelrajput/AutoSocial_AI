import os
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


class BrowserManager:
    """
    Starts and closes Chrome for local Selenium automation.

    Designed for:
    - user-device-based execution
    - existing Chrome login session reuse
    - social media automation workflows
    """

    def __init__(
        self,
        user_data_dir: Optional[str] = None,
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
        Validate the Chrome user data directory if provided.
        """
        if self.user_data_dir:
            profile_root = Path(self.user_data_dir)
            if not profile_root.exists():
                raise FileNotFoundError(
                    f"Chrome user data directory not found: {self.user_data_dir}"
                )

    def _build_options(self) -> Options:
            """
            Build Chrome options.
            """
            options = Options()

            # hide Chrome internal logs in terminal
            options.add_experimental_option(
                "excludeSwitches",
                ["enable-automation", "enable-logging"],
            )
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")

            # basic browser behavior
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # reduce automation detection
            options.add_experimental_option("useAutomationExtension", False)

            # keep browser open after script ends
            options.add_experimental_option("detach", self.detach)

            # use user's existing Chrome profile/session
            if self.user_data_dir:
                options.add_argument(f"--user-data-dir={self.user_data_dir}")
                options.add_argument(f"--profile-directory={self.profile_directory}")

            # headless is not recommended for social media automation
            if self.headless:
                options.add_argument("--headless=new")

            return options

    def start_browser(self) -> WebDriver:
        """
        Start Chrome browser and return the driver instance.
        """
        self._validate_profile_path()
        options = self._build_options()

        try:
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(5)

            # hide webdriver flag a bit more
            try:
                driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
            except Exception:
                pass

            return driver
        except WebDriverException as exc:
            raise RuntimeError(f"Failed to start Chrome browser: {exc}")

    @staticmethod
    def close_browser(driver: Optional[WebDriver]) -> None:
        """
        Close browser safely.
        """
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    """
    Local test run:
    - opens Chrome
    - navigates to Google
    """

    chrome_user_data = os.getenv(
    "CHROME_USER_DATA_DIR",
    os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")
)

    manager = BrowserManager(
        user_data_dir=chrome_user_data,
        profile_directory="Default",
        detach=True,
        headless=False,
    )

    driver = None
    try:
        driver = manager.start_browser()
        time.sleep(3)
        driver.get("https://www.google.com")
        print("Browser started successfully.")
    except Exception as error:
        print(f"Error: {error}")
    finally:
        pass