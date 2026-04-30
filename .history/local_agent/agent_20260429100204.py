import asyncio
import contextlib
import json
import os
import sys
import getpass
from pathlib import Path

import requests
import websockets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from automation_engine.executor.task_runner import run_task
from automation_engine.browser.browser_manager import BrowserManager


DJANGO_BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{DJANGO_BASE_URL}/accounts/login/"

CONFIG_FILE = os.path.join(BASE_DIR, "agent_config.json")


def log(message):
    print(message)


# ===============================
# 🔐 AUTH
# ===============================
def get_agent_token():
    env_token = os.getenv("AGENT_TOKEN")
    if env_token:
        log("✅ Agent token loaded from environment")
        return env_token

    log("🔐 Please login to connect local agent")

    email = input("Enter email: ").strip()
    password = getpass.getpass("Enter password: ").strip()

    response = requests.post(
        LOGIN_URL,
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


# ===============================
# 💾 PROFILE CONFIG
# ===============================
def load_or_create_profile():
    """
    Load profile config or ask user once.
    """

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        log("✅ Loaded saved Chrome profile")
        return config["user_data_dir"], config["profile_directory"]

    # First-time setup
    user_data_dir, profile_directory = BrowserManager.ask_profile_setup()

    config = {
        "user_data_dir": user_data_dir,
        "profile_directory": profile_directory,
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    log("💾 Chrome profile saved for future use")

    return user_data_dir, profile_directory


# ===============================
# 🤖 TASK EXECUTION
# ===============================
def run_task_silently(post_id, platform, caption, media, browser):
    """
    Run automation silently but with correct browser.
    """
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            return run_task(post_id, platform, caption, media, browser)


# ===============================
# 🔌 MAIN LOOP
# ===============================
async def main():
    agent_token = get_agent_token()

    # 🔥 Load Chrome profile
    user_data_dir, profile_directory = load_or_create_profile()

    browser_manager = BrowserManager(
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        detach=True,
        headless=False,
    )

    server_url = f"ws://127.0.0.1:8000/ws/agent/?token={agent_token}"

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
                            browser_manager,  # 🔥 pass browser manager
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

        except Exception:
            log("❌ Connection lost, retrying in 5 seconds...")

            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                log("\nAgent stopped.")
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\nAgent stopped by user.")
    except asyncio.CancelledError:
        log("\nAgent cancelled.")