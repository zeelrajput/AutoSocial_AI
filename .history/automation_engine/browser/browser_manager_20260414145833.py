import os
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


class BrowserManager:

    def __init__(
        self,
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default",
        detach: bool = True,
        headless: bool = False
    ):
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        self.detach = detach
        self.headless = headless

    def _validate_profile_path(self):
        if self.user_data_dir:
            profile_root = Path(self.user_data_dir)
            if not profile_root.exists():
                raise FileNotFoundError(
                    f"Chrome user data directory not found: {self.user_data_dir}"
                )

    def _build_options(self):
        options = Options()

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-default-browser-check")

        options.add_experimental_option("detach", self.detach)

        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument(f"--profile-directory={self.profile_directory}")

        if self.headless:
            options.add_argument("--headless=new")

        return options

    def start_browser(self):
        self._validate_profile_path()
        options = self._build_options()

        try:
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as exc:
            raise RuntimeError(f"Failed to start Chrome browser: {exc}")

    @staticmethod
    def close_browser(driver: Optional[webdriver.Chrome]):
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# ✅ TEST BLOCK
if __name__ == "__main__":

    chrome_user_data = os.getenv(
        "CHROME_USER_DATA_DIR",
        r"C:\Users\HP\AppData\Local\Google\Chrome\User Data"
    )

    manager = BrowserManager(
        user_data_dir=chrome_user_data,
        profile_directory="Default",
        detach=True,
        headless=False,
    )

    try:
        driver = manager.start_browser()
        driver.get("https://www.google.com")
        print("Browser started successfully")

    except Exception as error:
        print(f"Error: {error}")