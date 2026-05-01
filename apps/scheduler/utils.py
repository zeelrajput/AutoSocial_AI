from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.posts.models import PostMedia


def send_task_to_agent(post):
    channel_layer = get_channel_layer()

    media_paths = []

    post_media_qs = PostMedia.objects.filter(post=post)

    for media in post_media_qs:
        if media.file:
            media_paths.append(media.file.path)

    print("📡 Sending to group:", f"agent_{post.user_id}")
    print("📦 Post ID:", post.id)
    print("📸 Media paths:", media_paths)

    async_to_sync(channel_layer.group_send)(
        f"agent_{post.user_id}",
        {
            "type": "send_task",
            "post_id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media": media_paths,
        }
    )