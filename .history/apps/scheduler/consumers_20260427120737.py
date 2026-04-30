import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.posts.models import Post


class AgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"agent_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "connected",
            "message": "Agent connected successfully"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("Received from agent:", data)

        if data.get("type") == "task_result":
            await self.update_post_status(data)

   @sync_to_async
def update_post_status(self, data):
    post_id = data.get("post_id")
    success = data.get("success")
    message = data.get("message", "")

    try:
        post = Post.objects.get(id=post_id)

        if success:
            post.status = "posted"
        else:
            post.status = "failed"

        try:
            post.error_message = None if success else message
            post.save(update_fields=["status", "error_message"])
        except Exception:
            post.save(update_fields=["status"])

        print(f"✅ Post {post_id} status updated to {post.status}")

    except Post.DoesNotExist:
        print(f"❌ Post {post_id} not found")
    except Exception as e:
        print(f"❌ Status update error:", str(e))
        
    async def send_task(self, event):
        await self.send(text_data=json.dumps({
            "type": "task",
            "post_id": event["post_id"],
            "platform": event["platform"],
            "caption": event["caption"],
            "media": event.get("media"),
        }))