import asyncio
import json
import os
import sys
import websockets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from automation_engine.executor.task_runner import run_task


import os

AGENT_TOKEN = os.getenv("AGENT_TOKEN")

if not AGENT_TOKEN:
    AGENT_TOKEN = input("Enter your agent token: ").strip()

SERVER_URL = f"ws://127.0.0.1:8000/ws/agent/?token={AGENT_TOKEN}"

async def main():
    while True:
        try:
            print("Connecting to Django server...")

            async with websockets.connect(
                    SERVER_URL,
                    ping_interval=None,
                    ping_timeout=None
                ) as websocket:
                print("Agent connected to Django server")

                async for message in websocket:
                    data = json.loads(message)
                    print("Received from server:", data)

                    if data.get("type") == "task":
                        post_id = data.get("post_id")
                        platform = data.get("platform")
                        caption = data.get("caption")
                        media = data.get("media") or []

                        if isinstance(media, str):
                            media = [media]

                        print("Running task...")
                        print("Post ID:", post_id)
                        print("Platform:", platform)
                        print("Caption:", caption)
                        print("Media:", media)
                        
                        try:
                            print("🔥 Calling run_task now...")
                            result = await asyncio.to_thread(
                                    run_task,
                                    post_id,
                                    platform,
                                    caption,
                                    media
                                )
                            print("🔥 run_task result:", result)
                            await websocket.send(json.dumps({
                                "type": "task_result",
                                "post_id": post_id,
                                "success": result.get("success", False),
                                "message": result.get("message", "")
                            }))

                            print("✅ Result sent to Django:", result)

                        except Exception as e:
                            await websocket.send(json.dumps({
                                "type": "task_result",
                                "post_id": post_id,
                                "success": False,
                                "message": str(e)
                            }))

        except KeyboardInterrupt:
            print("\nAgent stopped by user.")
            break

        except asyncio.CancelledError:
            print("\nAgent cancelled.")
            break

        except Exception as e:
            print("Connection error:", e)
            print("Retrying in 5 seconds...")

            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                print("\nAgent stopped.")
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
    except asyncio.CancelledError:
        print("\nAgent cancelled.")