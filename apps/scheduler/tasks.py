from celery import shared_task
from django.utils import timezone

# pyrefly: ignore [missing-import]
from apps.posts.models import Post
# pyrefly: ignore [missing-import]
from apps.scheduler.utils import send_task_to_agent


@shared_task
def check_scheduled_posts(user_id=None):
    now = timezone.now()

    posts = Post.objects.filter(
        status="scheduled",
        scheduled_time__lte=now
    )

    if user_id:
        posts = posts.filter(user_id=user_id)

    count = posts.count()

    for post in posts:
        print(f"🚀 Sending post {post.id} ({post.platform}) to agent")

        post.status = "processing"
        post.save(update_fields=["status"])

        send_task_to_agent(post)

    return f"Sent {count} posts to agent"