from celery import shared_task
from django.utils import timezone

from apps.posts.models import Post


@shared_task
def check_scheduled_posts():
    now = timezone.now()

    posts = Post.objects.filter(
        status="scheduled",
        scheduled_time__lte=now
    )

    for post in posts:
        print("Scheduled post found:", post.id, post.platform)

    return f"Checked posts: {posts.count()}"