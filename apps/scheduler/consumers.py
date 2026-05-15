import json
import random
import asyncio
import hashlib
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

# pyrefly: ignore [missing-import]
from apps.posts.models import Post
# pyrefly: ignore [missing-import]
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
            self.group_name = f"agent_{self.user_id}"
            print("✅ Agent joined group:", self.group_name)

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

        if data.get("type") == "comment_check_result":
            new_comments, post_url = await self.handle_comment_result(data)
            
            for c in new_comments:
                if c.get("reply_text") and post_url:
                    # Add random delay (20–90 sec) for natural behavior
                    delay = random.randint(20, 90)
                    print(f"⏳ Waiting {delay} seconds before sending auto-reply to {c.get('author')}...")
                    await asyncio.sleep(delay)
                    
                    print(f"🤖 Sending auto-reply for comment {c['id']}")
                    await self.send(text_data=json.dumps({
                        "type": "reply_comment",
                        "comment_id": c["id"],
                        "platform": c["platform"],
                        "reply_text": c["reply_text"],
                        "post_url": post_url,
                        "author": c.get("author"),
                        "comment_text": c.get("comment_text"),
                    }))

        if data.get("type") == "reply_comment_result":
            success = data.get("success", False)
            comment_id = data.get("comment_id")
            print("✅ Reply result:", data)
            if success and comment_id:
                await self.mark_comment_replied(comment_id)

    @sync_to_async
    def update_post_status(self, data):
        post_id = data.get("post_id")
        success = data.get("success")
        message = data.get("message", "")
        post_url = data.get("post_url")

        try:
            post = Post.objects.get(id=post_id, user_id=self.user_id)

            if success:
                post.status = "posted"

                if post_url:
                    post.post_url = post_url
            else:
                post.status = "failed"

            try:
                post.error_message = None if success else message

                update_fields = ["status", "error_message"]

                if success and post_url:
                    update_fields.append("post_url")

                post.save(update_fields=update_fields)

            except Exception:
                update_fields = ["status"]

                if success and post_url:
                    update_fields.append("post_url")

                post.save(update_fields=update_fields)

            print(f"✅ Post {post_id} status updated to {post.status}")
            if post_url:
                print(f"🔗 Post URL saved: {post_url}")

        except Post.DoesNotExist:
            print(f"❌ Post {post_id} not found")
        except Exception as e:
            print("❌ Status update error:", str(e))

    @sync_to_async
    def mark_comment_replied(self, comment_id):
        # pyrefly: ignore [missing-import]
        from apps.comments.models import PostComment
        try:
            comment = PostComment.objects.get(id=comment_id)
            comment.status = "replied"
            comment.save(update_fields=["status"])
            print(f"✅ Comment {comment_id} marked as replied")
        except PostComment.DoesNotExist:
            print(f"❌ Comment {comment_id} not found")
        except Exception as e:
            print(f"❌ mark_comment_replied error: {e}")


    async def send_task(self, event):
        await self.send(text_data=json.dumps({
            "type": "task",
            "post_id": event["post_id"],
            "platform": event["platform"],
            "caption": event["caption"],
            "media": event.get("media"),
        }))

    async def send_check_comments(self, event):

        await self.send(text_data=json.dumps({
            "type": "check_comments",

            "post_id": event["post_id"],
            "platform": event["platform"],
            "post_url": event["post_url"],
        }))


    async def send_reply_comment(self, event):

        await self.send(text_data=json.dumps({
            "type": "reply_comment",

            "comment_id": event["comment_id"],
            "platform": event["platform"],
            "reply_text": event["reply_text"],
            "post_url": event["post_url"],
        }))

    @sync_to_async
    def handle_comment_result(self, data):

        # pyrefly: ignore [missing-import]
        from apps.comments.services import create_comment_if_new

        post_id = data.get("post_id")
        comments = data.get("comments", [])
        
        print(f"📥 Received {len(comments)} comments from agent for post {post_id}")
        
        new_comments = []
        post_url = data.get("post_url")

        try:
            post = Post.objects.get(
                id=post_id,
                user_id=self.user_id
            )
            
            if not post_url:
                post_url = getattr(post, "post_url", "")

            for item in comments:
                author = item.get("author")
                text = item.get("text")
                print(f"🧐 Processing comment: [{author}] - {text}")

                comment = create_comment_if_new(
                    post=post,
                    platform=post.platform,
                    author=author,
                    text=text,
                )

                if comment:
                    print(f"✅ New comment saved: {comment.id}. AI Reply: {comment.reply_text}")
                    new_comments.append({
                        "id": comment.id,
                        "platform": comment.platform,
                        "reply_text": comment.reply_text,
                        "author": comment.comment_author,
                        "comment_text": comment.comment_text,
                    })
                    break  # One response according to one comment at a time
                else:
                    print(f"⏭️ Comment skipped (duplicate or error)")

        except Exception as e:
            print("Comment save error:", e)
            
        return new_comments, post_url