from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_check_comments_task(post):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"agent_{post.user.id}",
        {
            "type": "send_check_comments",

            "post_id": post.id,
            "platform": post.platform,

            # temporary
            "post_url": getattr(post, "post_url", ""),
        }
    )


def send_reply_comment_task(comment):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"agent_{comment.user.id}",
        {
            "type": "send_reply_comment",

            "comment_id": comment.id,
            "platform": comment.platform,
            "reply_text": comment.reply_text,

            "post_url": getattr(comment.post, "post_url", ""),
        }
    )