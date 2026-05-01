import asyncio
import contextlib
import json
import os
import sys
import getpass
from pathlib import Path

import requests
import websockets

# BEFORE
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, BASE_DIR)

# AFTER
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = PROJECT_ROOT / "core"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(CORE_DIR))

from automation_engine.executor.task_runner import run_task
from automation_engine.browser.browser_manager import BrowserManager


# BEFORE
# DJANGO_BASE_URL = "http://127.0.0.1:8000"
# LOGIN_URL = f"{DJANGO_BASE_URL}/accounts/login/"

# AFTER
# Base URL will come from agent_live.py or agent_local.py


# BEFORE
# CONFIG_FILE = os.path.join(BASE_DIR, "agent_config.json")

# AFTER
APP_DATA_DIR = Path(os.getenv("LOCALAPPDATA")) / "AutoSocialAI"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA_DIR / "agent_config.json"


def log(message):
    print(message)


def make_ws_url(base_url, agent_token):
    """
    AFTER:
    Convert normal HTTP/HTTPS base URL into WebSocket URL.
    http  -> ws
    https -> wss
    """

    if base_url.startswith("https://"):
        ws_base_url = base_url.replace("https://", "wss://", 1)
    else:
        ws_base_url = base_url.replace("http://", "ws://", 1)

    return f"{ws_base_url}/ws/agent/?token={agent_token}"


# BEFORE
# def get_agent_token():

# AFTER
def get_agent_token(base_url):
    env_token = os.getenv("AGENT_TOKEN")
    if env_token:
        log("✅ Agent token loaded from environment")
        return env_token

    # AFTER
    login_url = f"{base_url}/accounts/login/"

    log("🔐 Please login to connect local agent")

    email = input("Enter email: ").strip()
    password = getpass.getpass("Enter password: ").strip()

    response = requests.post(
        login_url,
        json={
            "email": email,
            "password": password,
            "device_name": "Windows Agent",
        },
        timeout=20,
    )

    data = response.json()

    if not data.get("success"):
        raise Exception(data.get("message", "Login failed"))

    log("✅ Login successful")
    return data["agent_token"]


def open_profile_for_platform_login(user_data_dir, profile_directory):
    import subprocess

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        print("❌ Chrome not found")
        return

    urls = [
        "https://www.instagram.com/",
        "https://www.facebook.com/",
        "https://www.linkedin.com/feed/",
        "https://x.com/",
    ]

    subprocess.Popen([
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_directory}",
        *urls,
    ])

    print("\n👉 Login to all platforms")
    input("After login, close Chrome and press ENTER...")


def load_or_create_profile():
    """
    Load saved Chrome profile or allow user to change it.
    """

    if CONFIG_FILE.exists():
        print("\n⚙️ Chrome Profile Found")
        print("1. Use saved profile")
        print("2. Change / Select new profile")

        choice = input("Select option: ").strip()

        if choice == "1":
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            print("✅ Using saved profile")
            return config["user_data_dir"], config["profile_directory"]

        print("🔄 Changing profile...")

    user_data_dir, profile_directory = BrowserManager.ask_profile_setup()

    config = {
        "user_data_dir": user_data_dir,
        "profile_directory": profile_directory,
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print("💾 Profile updated successfully")

    open_profile_for_platform_login(user_data_dir, profile_directory)

    return user_data_dir, profile_directory


def run_task_silently(post_id, platform, caption, media, browser):
    """
    Run automation silently but with correct browser manager.
    """

    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            return run_task(post_id, platform, caption, media, browser)


# BEFORE
# async def main():

# AFTER
async def main(base_url: str):
    log(f"🌐 Base URL: {base_url}")

    # BEFORE
    # agent_token = get_agent_token()

    # AFTER
    agent_token = get_agent_token(base_url)

    user_data_dir, profile_directory = load_or_create_profile()

    browser_manager = BrowserManager(
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        detach=True,
        headless=False,
    )

    # BEFORE
    # server_url = f"ws://127.0.0.1:8000/ws/agent/?token={agent_token}"

    # AFTER
    server_url = make_ws_url(base_url, agent_token)
    # log(f"🔌 WebSocket URL: {server_url}")

    while True:
        try:
            log("🔄 Connecting to server...")

            async with websockets.connect(
                server_url,
                ping_interval=None,
                ping_timeout=None,
            ) as websocket:
                log("✅ Agent connected")

                async for message in websocket:
                    data = json.loads(message)

                    if data.get("type") != "task":
                        continue

                    post_id = data.get("post_id")
                    platform = data.get("platform")
                    caption = data.get("caption")
                    media = data.get("media") or []

                    if isinstance(media, str):
                        media = [media]

                    log("📩 Task received")
                    log(f"📱 Platform: {platform}")
                    log("🚀 Starting automation...")

                    try:
                        result = await asyncio.to_thread(
                            run_task_silently,
                            post_id,
                            platform,
                            caption,
                            media,
                            browser_manager,
                        )

                        await websocket.send(json.dumps({
                            "type": "task_result",
                            "post_id": post_id,
                            "success": result.get("success", False),
                            "message": result.get("message", ""),
                        }))

                        if result.get("success"):
                            log("✅ Automation completed")
                        else:
                            log("❌ Automation failed")

                    except Exception as e:
                        await websocket.send(json.dumps({
                            "type": "task_result",
                            "post_id": post_id,
                            "success": False,
                            "message": str(e),
                        }))

                        log("❌ Automation failed")
                        log(f"Error: {e}")

        except KeyboardInterrupt:
            log("\nAgent stopped by user.")
            break

        except asyncio.CancelledError:
            log("\nAgent cancelled.")
            break

        except Exception as e:
            log(f"❌ Connection lost: {e}")
            log("Retrying in 5 seconds...")

            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                log("\nAgent stopped.")
                break


# BEFORE
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         log("\nAgent stopped by user.")
#     except asyncio.CancelledError:
#         log("\nAgent cancelled.")

# AFTER
# Do not run directly from agent.py.
# Run using agent_live.py or agent_local.py.