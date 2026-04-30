import asyncio
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


DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://127.0.0.1:8000")
BASE_WS_URL = os.getenv("BASE_WS_URL", "ws://127.0.0.1:8000")

LOGIN_URL = f"{DJANGO_BASE_URL}/accounts/login/"
CONFIG_FILE = os.path.join(BASE_DIR, "agent_config.json")


def log(message):
    print(message, flush=True)


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

    try:
        response = requests.post(
            LOGIN_URL,
            json={
                "email": email,
                "password": password,
                "device_name": "Windows Agent",
            },
            timeout=20,
        )
    except Exception as e:
        raise Exception(f"Login request failed: {str(e)}")

    if response.status_code != 200:
        raise Exception(f"Login API failed with status {response.status_code}: {response.text[:300]}")

    try:
        data = response.json()
    except Exception:
        raise Exception("Invalid login response from server. Server did not return JSON.")

    if not data.get("success"):
        raise Exception(data.get("message", "Login failed"))

    agent_token = data.get("agent_token")

    if not agent_token:
        raise Exception("Login successful but agent_token missing from response")

    log("✅ Login successful")
    return agent_token


# ===============================
# 💾 PROFILE CONFIG
# ===============================
def load_or_create_profile():
    """
    Load saved Chrome profile or allow user to change it.
    """

    if os.path.exists(CONFIG_FILE):
        print("\n⚙️ Chrome Profile Found")
        print("1. Use saved profile")
        print("2. Change / Select new profile")

        choice = input("Select option: ").strip()

        if choice == "1":
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)

                user_data_dir = config.get("user_data_dir")
                profile_directory = config.get("profile_directory", "Default")

                if not user_data_dir:
                    raise Exception("user_data_dir missing in config")

                print("✅ Using saved profile")
                print(f"📁 Profile path: {user_data_dir}")
                print(f"👤 Profile directory: {profile_directory}")

                return user_data_dir, profile_directory

            except Exception as e:
                print(f"⚠️ Saved profile config invalid: {e}")
                print("🔄 Please select Chrome profile again")

        else:
            print("🔄 Changing profile...")

    user_data_dir, profile_directory = BrowserManager.ask_profile_setup()

    config = {
        "user_data_dir": user_data_dir,
        "profile_directory": profile_directory,
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    print("💾 Profile updated successfully")

    return user_data_dir, profile_directory


# ===============================
# 🧹 NORMALIZE MEDIA
# ===============================
def normalize_media(media):
    if not media:
        return []

    if isinstance(media, list):
        return media

    if isinstance(media, str):
        return [media]

    return [media]


# ===============================
# 🔌 MAIN LOOP
# ===============================
async def main():
    agent_token = get_agent_token()

    user_data_dir, profile_directory = load_or_create_profile()

    browser_manager = BrowserManager(
        user_data_dir=user_data_dir,
        profile_directory=profile_directory,
        detach=True,
        headless=False,
    )

    server_url = f"{BASE_WS_URL}/ws/agent/?token={agent_token}"

    while True:
        try:
            log("🔄 Connecting to server...")

            async with websockets.connect(
                server_url,
                ping_interval=30,
                ping_timeout=30,
                close_timeout=10,
            ) as websocket:

                log("✅ Agent connected")

                async for message in websocket:
                    try:
                        data = json.loads(message)
                    except Exception:
                        log("⚠️ Invalid message received from server")
                        continue

                    if data.get("type") != "task":
                        continue

                    post_id = data.get("post_id")
                    platform = data.get("platform")
                    caption = data.get("caption") or ""
                    media = normalize_media(data.get("media"))

                    log("📩 Task received")
                    log(f"🆔 Post ID: {post_id}")
                    log(f"📱 Platform: {platform}")
                    log(f"📝 Caption: {caption}")
                    log(f"🖼 Media: {media}")
                    log("🚀 Starting automation...")

                    try:
                        result = await asyncio.to_thread(
                            run_task,
                            post_id,
                            platform,
                            caption,
                            media,
                            browser_manager,
                        )

                        if not result:
                            result = {
                                "success": False,
                                "message": "Automation returned empty result",
                            }

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
                            log(f"Reason: {result.get('message', '')}")

                    except Exception as e:
                        error_message = f"Agent task error: {str(e)}"

                        await websocket.send(json.dumps({
                            "type": "task_result",
                            "post_id": post_id,
                            "success": False,
                            "message": error_message,
                        }))

                        log("❌ Automation failed")
                        log(error_message)

        except KeyboardInterrupt:
            log("\nAgent stopped by user.")
            break

        except asyncio.CancelledError:
            log("\nAgent cancelled.")
            break

        except Exception as e:
            log(f"❌ Connection lost: {str(e)}")
            log("🔄 Retrying in 5 seconds...")

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