from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.posts.models import Post


def send_post_to_agent(post):
    channel_layer = get_channel_layer()

    media_path = None
    if post.media:
        media_path = post.media.path

    async_to_sync(channel_layer.group_send)(
        f"agent_{post.user.id}",
        {
            "type": "send_task",
            "post_id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media": media_path,
        }
    )


def run_schedular(request):
    now = timezone.now()

    pending_posts = Post.objects.filter(
        status="pending",
        scheduled_time__lte=now
    )

    processed_ids = []

    for post in pending_posts:
        # Do not run Selenium directly on server
        # Send task to user's local .exe agent
        send_post_to_agent(post)

        post.status = "scheduled"
        post.save(update_fields=["status"])

        processed_ids.append(post.id)

    return JsonResponse({
        "message": "scheduler sent tasks to local agent successfully",
        "processed_post_ids": processed_ids
    })


def send_task_to_agent(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    send_post_to_agent(post)

    post.status = "scheduled"
    post.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "message": "Task sent to local agent",
        "post_id": post.id,
        "platform": post.platform
    })