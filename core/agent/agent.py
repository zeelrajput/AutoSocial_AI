import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import asyncio
import contextlib
import json
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

from core.automation_engine.executor.task_runner import run_task
from core.automation_engine.browser.browser_manager import BrowserManager

APP_DATA_DIR = Path(os.getenv("LOCALAPPDATA")) / "AutoSocialAI"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = APP_DATA_DIR / "agent_config.json"


def log(message):
    print(message)

def safe_json(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)


def safe_json(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return obj


def make_ws_url(base_url, agent_token):
    if base_url.startswith("https://"):
        ws_base_url = base_url.replace("https://", "wss://", 1)
    else:
        ws_base_url = base_url.replace("http://", "ws://", 1)

    return f"{ws_base_url}/ws/agent/?token={agent_token}"


def get_agent_token(base_url):
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

    data = response.json()

    if response.status_code != 200:
        raise Exception(data.get("error", "Login failed"))

    # ✅ FIXED: only accept agent_token
    token = (
        data.get("agent_token")
        or data.get("data", {}).get("agent_token")
    )

    if not token:
        raise Exception("agent_token not found in response")

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
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                    max_size=None,
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

                                log("✅ Automation completed" if result.get("success") else "❌ Automation failed")

                            elif task_type == "check_comments":
                                post_url = data.get("post_url")

                                driver = browser_manager.start_browser()

                                try:
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
                                        "comments": safe_json(comments),
                                    }))

                                    log("💬 Comments checked")

                                finally:
                                    browser_manager.close_browser()

                            elif task_type == "reply_comment":
                                platform = data.get("platform")
                                post_url = data.get("post_url")
                                reply_text = data.get("reply_text")
                                author = data.get("author")
                                comment_text = data.get("comment_text")
                                comment_id = data.get("comment_id")

                                driver = browser_manager.start_browser()

                                try:
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
                                        "success": result.get("success", False),
                                        "message": result.get("message", ""),
                                        "comment_id": comment_id,
                                    }))

                                    log("🤖 Reply task completed")

                                except Exception as e:
                                    await websocket.send(json.dumps({
                                        "type": "reply_comment_result",
                                        "success": False,
                                        "message": str(e),
                                        "comment_id": comment_id,
                                    }))
                                    log(f"❌ Reply failed: {e}")

                                finally:
                                    browser_manager.close_browser()

                        except Exception as e:
                            await websocket.send(json.dumps({
                                "type": "task_result",
                                "post_id": post_id,
                                "success": False,
                                "message": str(e),
                            }))
                            log(f"❌ Automation failed: {e}")

            except websockets.ConnectionClosed as e:
                log(f"❌ Connection closed (code={e.code}, reason={e.reason or 'n/a'})")
                log("Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                log(f"❌ Connection error: {type(e).__name__}: {e}")
                log("Retrying in 5 seconds...")
                await asyncio.sleep(5)

    except KeyboardInterrupt:
        log("\nAgent stopped by user.")
    except Exception as e:
        log(f"❌ Fatal error: {e}")
    finally:
        log("👋 Agent shutdown complete.")