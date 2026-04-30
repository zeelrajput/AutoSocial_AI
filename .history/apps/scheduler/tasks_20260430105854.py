from celery import shared_task
from django.utils import timezone
from apps.posts.models import Post
from apps.scheduler.utils import send_task_to_agent


@shared_task
def check_scheduled_posts():
    now = timezone.now()

    posts = Post.objects.filter(
        status="scheduled",
        scheduled_time__lte=now
    )

    count = posts.count()

    for post in posts:
        print(f"🚀 Sending post {post.id} ({post.platform}) to agent")

        post.status = "processing"
        post.save(update_fields=["status"])

        send_task_to_agent(post)

    return f"Sent {count} posts to agent"