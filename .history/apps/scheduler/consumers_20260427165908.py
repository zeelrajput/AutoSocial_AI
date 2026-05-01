import json
import hashlib
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.posts.models import Post
from apps.accounts.models import User, AgentDevice


class AgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
    query_string = self.scope["query_string"].decode()
    params = parse_qs(query_string)
    raw_token = params.get("token", [None])[0]

    # NEW token-based route: /ws/agent/?token=...
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            device = await sync_to_async(
                AgentDevice.objects.select_related("user").get
            )(
                token_hash=token_hash,
                is_active=True
            )
        except AgentDevice.DoesNotExist:
            print("❌ Invalid agent token")
            await self.close()
            return

        self.user = device.user
        self.user_id = self.user.id
        self.group_name = f"agent_user_{self.user_id}"

    # OLD route: /ws/agent/5/
    else:
        user_id = self.scope["url_route"]["kwargs"].get("user_id")

        if not user_id:
            print("❌ No token or user_id provided")
            await self.close()
            return

        self.user_id = user_id
        self.group_name = f"agent_{self.user_id}"

    await self.channel_layer.group_add(
        self.group_name,
        self.channel_name
    )

    await self.accept()

    await self.send(text_data=json.dumps({
        "type": "connected",
        "message": "Agent connected successfully",
        "user_id": self.user_id
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
            # safer for token multi-user
            post = Post.objects.get(id=post_id, user_id=self.user_id)

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