import asyncio
import contextlib
import json
import os
import sys
import getpass
from pathlib import Path
import ssl
import requests
import websockets

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fix path for direct execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.automation_engine.executor.comment_task_runner import (
    run_check_comments_task,
    run_reply_comment_task,
)

browser_driver = None
browser_manager = None

from core.automation_engine.executor.task_runner import run_task
from core.automation_engine.browser.browser_manager import BrowserManager

APP_DATA_DIR = Path(os.getenv("LOCALAPPDATA")) / "AutoSocialAI"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA_DIR / "agent_config.json"


def log(message):
    print(message)


def make_ws_url(base_url, agent_token):
    """
    Convert normal HTTP/HTTPS base URL into WebSocket URL.
    http  -> ws
    https -> wss
    """

    if base_url.startswith("https://"):
        ws_base_url = base_url.replace("https://", "wss://", 1)
    else:
        ws_base_url = base_url.replace("http://", "ws://", 1)

    return f"{ws_base_url}/ws/agent/?token={agent_token}"


def get_agent_token(base_url):
    import requests
    import getpass

    email = input("Enter email: ")
    password = getpass.getpass("Enter password: ")

    login_url = f"{base_url}/accounts/login/"

    print(f"🔐 Login URL: {login_url}")

    response = requests.post(
        login_url,
        json={
            "email": email,
            "password": password,
            "device_name": "AutoSocial Local Agent"
        },
        timeout=20,
        verify=False
    )

    print("📡 Status Code:", response.status_code)
    print("📄 Response Text:", response.text[:500])

    try:
        data = response.json()
    except Exception:
        raise Exception(
            "Server did not return JSON. Check login API URL, server error, or CSRF/API issue."
        )

    if response.status_code != 200:
        raise Exception(data.get("error", "Login failed"))

    token = (
        data.get("agent_token")
        or data.get("data", {}).get("agent_token")
        or data.get("access")
        or data.get("data", {}).get("access")
    )

    if not token:
        raise Exception("Token not found in login response")

    print("✅ Login successful")
    return token


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

import tempfile

def download_media_file(media_url):
    temp_dir = Path(tempfile.gettempdir()) / "autosocial_media"
    temp_dir.mkdir(parents=True, exist_ok=True)

    filename = media_url.split("/")[-1].split("?")[0]
    local_path = temp_dir / filename

    response = requests.get(media_url, timeout=30, verify=False)
    response.raise_for_status()

    local_path.write_bytes(response.content)
    return str(local_path)

def run_task_silently(post_id, platform, caption, media, browser):
    """
    Run automation silently but with correct browser manager.
    """

    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            return run_task(post_id, platform, caption, media, browser)


async def main(base_url: str):
    log(f"🌐 Base URL: {base_url}")

    try:
        agent_token = get_agent_token(base_url)
        user_data_dir, profile_directory = load_or_create_profile()

        browser_manager = BrowserManager(
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
            detach=True,
            headless=False,
        )

        server_url = make_ws_url(base_url, agent_token)

        while True:
            try:
                log("🔄 Connecting to server...")

                ssl_context = None
                if server_url.startswith("wss://"):
                    ssl_context = ssl._create_unverified_context()

                async with websockets.connect(
                    server_url,
                    ping_interval=None,
                    ping_timeout=None,
                    ssl=ssl_context,
                ) as websocket:
                    log("✅ Agent connected")

                    async for message in websocket:
                        data = json.loads(message)
                        task_type = data.get("type")

                        if task_type not in ["task", "check_comments", "reply_comment"]:
                            continue

                        post_id = data.get("post_id")
                        platform = data.get("platform")
                        caption = data.get("caption")
                        media = data.get("media") or []

                        media = [
                            download_media_file(m) if isinstance(m, str) and m.startswith("http") else m
                            for m in media
                        ]

                        log("📩 Task received")
                        log(f"📱 Platform: {platform}")
                        log("🚀 Starting automation...")

                        try:
                            if task_type == "task":
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
                                    "post_url": result.get("post_url"),
                                }))

                                if result.get("success"):
                                    log("✅ Automation completed")
                                else:
                                    log("❌ Automation failed")

                            elif task_type == "check_comments":
                                post_url = data.get("post_url")
                                try:
                                    driver = browser_manager.start_browser()
                                    comments = await asyncio.to_thread(
                                        run_check_comments_task,
                                        driver,
                                        platform,
                                        post_url,
                                    )

                                    await websocket.send(json.dumps({
                                        "type": "comment_check_result",
                                        "post_id": post_id,
                                        "platform": platform,
                                        "comments": comments,
                                    }))
                                    log("💬 Comments checked")
                                finally:
                                    browser_manager.close_browser()

                            elif task_type == "reply_comment":
                                post_url = data.get("post_url")
                                reply_text = data.get("reply_text")
                                author = data.get("author")
                                comment_text = data.get("comment_text")
                                comment_id = data.get("comment_id")

                                try:
                                    driver = browser_manager.start_browser()
                                    result = await asyncio.to_thread(
                                        run_reply_comment_task,
                                        driver,
                                        platform,
                                        post_url,
                                        reply_text,
                                        author,
                                        comment_text,
                                    )

                                    await websocket.send(json.dumps({
                                        "type": "reply_comment_result",
                                        "success": result.get("success"),
                                        "message": result.get("message"),
                                        "comment_id": comment_id,
                                    }))
                                    log("🤖 Reply task completed")
                                finally:
                                    browser_manager.close_browser()

                        except Exception as e:
                            await websocket.send(json.dumps({
                                "type": "task_result",
                                "post_id": post_id,
                                "success": False,
                                "message": str(e),
                            }))
                            log("❌ Automation failed")
                            log(f"Error: {e}")

            except (websockets.ConnectionClosed, Exception) as e:
                log(f"❌ Connection error: {e}")
                log("Retrying in 5 seconds...")
                await asyncio.sleep(5)

    except KeyboardInterrupt:
        log("\nAgent stopped by user.")
    except asyncio.CancelledError:
        log("\nAgent cancelled.")
    except Exception as e:
        log(f"❌ Fatal error: {e}")
    finally:
        log("👋 Agent shutdown complete.")