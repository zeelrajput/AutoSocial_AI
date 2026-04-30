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
    Starts Chrome with Selenium using either:
    1. Existing Chrome profile
    2. Auto-created Selenium Chrome profile

    This helps new users keep login sessions after installing .exe.
    """

    def __init__(
        self,
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default",
        detach: bool = True,
        headless: bool = False,
    ) -> None:
        self.user_data_dir = user_data_dir or self.get_default_selenium_profile_dir()
        self.profile_directory = profile_directory
        self.detach = detach
        self.headless = headless

    @staticmethod
    def get_default_selenium_profile_dir() -> str:
        """
        Auto profile path for new users.
        Example:
        C:\\Users\\HP\\AppData\\Local\\AutoSocialAI\\chrome_profile
        """
        base_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.getcwd()),
            "AutoSocialAI",
            "chrome_profile",
        )
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    @staticmethod
    def ask_profile_setup() -> tuple[str, str]:
        """
        Terminal profile setup for .exe first run.
        """

        print("\n🔐 Chrome Profile Setup")
        print("1. Create new AutoSocial Chrome profile recommended")
        print("2. Use existing Chrome profile")

        choice = input("Select option 1 or 2: ").strip()

        if choice == "2":
            user_data_dir = input(
                r"Enter Chrome User Data path e.g. C:\Users\HP\AppData\Local\Google\Chrome\User Data: "
            ).strip()

            profile_directory = input(
                "Enter profile name e.g. Default / Profile 1 / Profile 2: "
            ).strip() or "Default"

        else:
            user_data_dir = BrowserManager.get_default_selenium_profile_dir()
            profile_directory = "Default"

            print("\n✅ New AutoSocial Chrome profile created:")
            print(user_data_dir)
            print("\n👉 Please follow these steps:\n")

            print("1. Press Win + R → type 'cmd' → press Enter")
            print("2. Paste the below command and press Enter:\n")

            print('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --user-data-dir="%LOCALAPPDATA%\\AutoSocialAI\\chrome_profile" --profile-directory="Default"\n')

            print("3. Login to LinkedIn, Instagram, Facebook, and X")
            print("4. Close Chrome")
            print("5. Come back here and press ENTER to continue\n")

            input("Press ENTER after completing the above steps...")

            print("💾 Profile updated successfully")

        return user_data_dir, profile_directory

    def _validate_profile_path(self) -> None:
        """
        Create profile folder if missing.
        """
        if self.user_data_dir:
            profile_root = Path(self.user_data_dir)
            profile_root.mkdir(parents=True, exist_ok=True)

    def _build_options(self) -> Options:
        """
        Build Chrome options.
        """
        options = Options()

        # Hide Chrome internal logs
        options.add_experimental_option(
            "excludeSwitches",
            ["enable-automation", "enable-logging"],
        )
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")

        # Basic browser behavior
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Reduce automation detection
        options.add_experimental_option("useAutomationExtension", False)

        # Keep browser open after script ends
        options.add_experimental_option("detach", self.detach)

        # Important: connect Selenium with Chrome profile
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_directory}")

        if self.headless:
            options.add_argument("--headless=new")

        return options

    def start_browser(self) -> WebDriver:
        """
        Start Chrome browser and return driver.
        """
        self._validate_profile_path()
        options = self._build_options()

        try:
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(5)

            try:
                driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
            except Exception:
                pass

            print("✅ Chrome opened successfully")
            print(f"📁 Profile path: {self.user_data_dir}")
            print(f"👤 Profile directory: {self.profile_directory}")

            return driver

        except WebDriverException as exc:
            raise RuntimeError(
                "Failed to start Chrome browser.\n"
                "Possible reasons:\n"
                "1. Chrome is already open with same profile\n"
                "2. Profile path is wrong\n"
                "3. ChromeDriver version issue\n\n"
                f"Original error: {exc}"
            )

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
    user_data_dir, profile_directory = BrowserManager.ask_profile_setup()

    manager = BrowserManager(
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        detach=True,
        headless=False,
    )

    driver = None

    try:
        driver = manager.start_browser()
        driver.get("https://www.google.com")
        time.sleep(3)
        print("Browser started successfully.")

    except Exception as error:
        print(f"❌ Error: {error}")

    finally:
        pass