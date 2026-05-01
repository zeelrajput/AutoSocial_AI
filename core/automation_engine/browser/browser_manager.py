import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


class BrowserManager:
    """
    Production-ready Chrome manager for AutoSocial AI.

    Option 1:
        Create/use AutoSocial Chrome profile.

    Option 2:
        Import existing Chrome profile into AutoSocial profile.
        Selenium does NOT run directly on user's real Chrome profile.
    """

    def __init__(
        self,
        user_data_dir: Optional[str] = None,
        profile_directory: str = "Default",
        detach: bool = True,
        headless: bool = False,
    ) -> None:
        self.user_data_dir = user_data_dir or self.get_autosocial_profile_dir()
        self.profile_directory = profile_directory
        self.detach = detach
        self.headless = headless

    # --------------------------------------------------
    # Paths
    # --------------------------------------------------

    @staticmethod
    def get_autosocial_profile_dir() -> str:
        path = Path(os.environ.get("LOCALAPPDATA", os.getcwd())) / "AutoSocialAI" / "chrome_profile"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @staticmethod
    def get_real_chrome_user_data_dir() -> Path:
        return Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"

    # --------------------------------------------------
    # Process cleanup
    # --------------------------------------------------

    @staticmethod
    def kill_chrome_processes() -> None:
        subprocess.call("taskkill /F /IM chromedriver.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call("taskkill /F /IM chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    # --------------------------------------------------
    # Profile detection
    # --------------------------------------------------

    @staticmethod
    def detect_chrome_profiles() -> Tuple[Path, list[str]]:
        base_path = BrowserManager.get_real_chrome_user_data_dir()

        if not base_path.exists():
            raise FileNotFoundError(f"Chrome User Data folder not found: {base_path}")

        profiles = []

        for folder in base_path.iterdir():
            if folder.is_dir() and (folder.name == "Default" or folder.name.startswith("Profile")):
                profiles.append(folder.name)

        if not profiles:
            raise RuntimeError("No Chrome profiles found.")

        return base_path, profiles

    # --------------------------------------------------
    # Import existing profile safely
    # --------------------------------------------------

    @staticmethod
    def import_existing_profile(source_user_data_dir: Path, source_profile_name: str) -> Tuple[str, str]:
        source_profile_path = source_user_data_dir / source_profile_name

        if not source_profile_path.exists():
            raise FileNotFoundError(f"Selected Chrome profile not found: {source_profile_path}")

        BrowserManager.kill_chrome_processes()

        target_user_data_dir = Path(BrowserManager.get_autosocial_profile_dir())
        target_profile_path = target_user_data_dir / "Default"

        if target_user_data_dir.exists():
            shutil.rmtree(target_user_data_dir)

        target_user_data_dir.mkdir(parents=True, exist_ok=True)

        ignore_items = shutil.ignore_patterns(
            "SingletonLock",
            "SingletonSocket",
            "SingletonCookie",
            "Crashpad",
            "ShaderCache",
            "GrShaderCache",
            "GPUCache",
            "Code Cache",
            "BrowserMetrics",
            "OptimizationGuidePredictionModels",
        )

        shutil.copytree(
            source_profile_path,
            target_profile_path,
            ignore=ignore_items,
        )

        local_state_file = source_user_data_dir / "Local State"
        if local_state_file.exists():
            shutil.copy2(local_state_file, target_user_data_dir / "Local State")

        print("✅ Existing Chrome profile imported successfully.")
        print(f"📁 AutoSocial profile path: {target_user_data_dir}")

        return str(target_user_data_dir), "Default"

    # --------------------------------------------------
    # Setup menu
    # --------------------------------------------------

    @staticmethod
    def ask_profile_setup() -> Tuple[str, str]:
        print("\n🔐 Chrome Profile Setup")
        print("1. Create new AutoSocial Chrome profile recommended")
        print("2. Import existing Chrome profile")

        choice = input("Select option 1 or 2: ").strip()

        if choice == "2":
            source_user_data_dir, profiles = BrowserManager.detect_chrome_profiles()

            print("\n🔍 Available Chrome Profiles:")
            for index, profile in enumerate(profiles, start=1):
                print(f"{index}. {profile}")

            selected = input("Select profile number: ").strip()

            try:
                selected_index = int(selected) - 1
                selected_profile = profiles[selected_index]
            except Exception:
                raise ValueError("Invalid profile selection.")

            user_data_dir, profile_directory = BrowserManager.import_existing_profile(
                source_user_data_dir,
                selected_profile,
            )

            print("💾 Imported profile saved successfully.")
            return user_data_dir, profile_directory

        user_data_dir = BrowserManager.get_autosocial_profile_dir()
        profile_directory = "Default"

        print("\n✅ AutoSocial Chrome profile ready:")
        print(user_data_dir)
        print("💾 Profile updated successfully")

        return user_data_dir, profile_directory

    # --------------------------------------------------
    # Chrome options
    # --------------------------------------------------

    def _validate_profile_path(self) -> None:
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

    def _build_options(self) -> Options:
        options = Options()

        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_directory}")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-background-mode")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--remote-debugging-port=0")

        options.add_experimental_option("detach", self.detach)
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "excludeSwitches",
            ["enable-automation", "enable-logging"],
        )

        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")

        if self.headless:
            options.add_argument("--headless=new")

        return options

    # --------------------------------------------------
    # Start browser
    # --------------------------------------------------

    def start_browser(self) -> WebDriver:
        self._validate_profile_path()

        BrowserManager.kill_chrome_processes()

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
                "Permanent fix suggestion:\n"
                "1. Use AutoSocial profile only\n"
                "2. Do not run Selenium directly on real Chrome profile\n"
                "3. Import existing profile using Option 2\n\n"
                f"Original error: {exc}"
            )

    # --------------------------------------------------
    # Close browser
    # --------------------------------------------------

    @staticmethod
    def close_browser(driver: Optional[WebDriver]) -> None:
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
        time.sleep(5)

    except Exception as error:
        print(f"❌ Error: {error}")

    finally:
        pass