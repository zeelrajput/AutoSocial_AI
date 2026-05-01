import asyncio
import json
import os
import sys
import getpass

import requests
import websockets


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from automation_engine.executor.task_runner import run_task


DJANGO_BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{DJANGO_BASE_URL}/accounts/login/"


def log(message):
    """
    Show clean user-friendly terminal messages.
    """
    print(message)


def get_agent_token():
    """
    Login user with email/password and get agent token from Django.
    """

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


async def main():
    agent_token = get_agent_token()
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

                    if data.get("type") == "task":
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
                                run_task,
                                post_id,
                                platform,
                                caption,
                                media,
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

                            log("📤 Result sent to server")

                        except Exception as e:
                            await websocket.send(json.dumps({
                                "type": "task_result",
                                "post_id": post_id,
                                "success": False,
                                "message": str(e),
                            }))

                            log("❌ Automation failed")
                            log("📤 Error result sent to server")

        except KeyboardInterrupt:
            log("\nAgent stopped by user.")
            break

        except asyncio.CancelledError:
            log("\nAgent cancelled.")
            break

        except Exception:
            log("❌ Connection lost, retrying...")

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