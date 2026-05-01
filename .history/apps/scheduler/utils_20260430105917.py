from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_task_to_agent(post):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"agent_{post.user.id}",
        {
            "type": "send_task",
            "post_id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media": post.media.path if post.media else None,
        }
    )