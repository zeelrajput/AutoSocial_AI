from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

from apps.posts.models import PostMedia


def send_task_to_agent(post):
    channel_layer = get_channel_layer()

    media_urls = []
    base_url = getattr(settings, "SITE_BASE_URL", "https://agents.zettalgor.com")

    post_media_qs = PostMedia.objects.filter(post=post)

    for media in post_media_qs:
        if media.file:
            media_urls.append(f"{base_url}{media.file.url}")

    print("📡 Sending to group:", f"agent_{post.user_id}")
    print("📦 Post ID:", post.id)
    print("📸 Media URLs:", media_urls)

    async_to_sync(channel_layer.group_send)(
        f"agent_{post.user_id}",
        {
            "type": "send_task",
            "post_id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media": media_urls,
        }
    )