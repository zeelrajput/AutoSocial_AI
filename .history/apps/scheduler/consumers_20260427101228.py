import json
from channels.generic.websocket import AsyncWebsocketConsumer


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

    async def send_task(self, event):
        await self.send(text_data=json.dumps({
            "type": "task",
            "post_id": event["post_id"],
            "platform": event["platform"],
            "caption": event["caption"],
            "media": event.get("media"),
        }))