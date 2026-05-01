from django.utils import timezone
import time
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.posts.models import Post


def send_post_to_agent(post):
    channel_layer = get_channel_layer()

    media_paths = [m.file.path for m in post.media_files.all()]
    if not media_paths and post.media:
        media_paths = [post.media.path]

    group_name = f"agent_{post.user.id}"

    print("Sending task to group:", group_name)
    print("Post ID:", post.id)
    print("Post User ID:", post.user.id)
    print("Platform:", post.platform)
    print("Media:", media_paths)

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_task",
            "post_id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media": media_paths,
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
        send_post_to_agent(post)

        post.status = "scheduled"
        post.save(update_fields=["status"])

        processed_ids.append(post.id)

         time.sleep(15)

    return JsonResponse({
        "success": True,
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
        "user_id": post.user.id,
        "platform": post.platform
    })