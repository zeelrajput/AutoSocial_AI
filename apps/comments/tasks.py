from celery import shared_task


@shared_task
def check_post_comments():
    # pyrefly: ignore [missing-import]
    from apps.posts.models import Post
    # pyrefly: ignore [missing-import]
    from apps.comments.models import CommentSettings
    # pyrefly: ignore [missing-import]
    from apps.comments.websocket import send_check_comments_task
    # pyrefly: ignore [missing-import]
    from apps.scheduler.tasks import check_scheduled_posts

    posts = Post.objects.filter(
        status="posted"
    )

    handled_posting_users = set()

    for post in posts:
        # Fetch or create settings for the user
        settings, _ = CommentSettings.objects.get_or_create(user=post.user)

        if settings.is_comment_detection_on:
            post_url = getattr(post, "post_url", "")

            if not post_url:
                print(f"⏭️ Skipping post {post.id}: post_url missing")
                continue

            print(f"💬 Checking comments for post {post.id}")
            send_check_comments_task(post)
        else:
            # If detection is off, run normal posting code for this user (once per task run)
            if post.user_id not in handled_posting_users:
                print(f"⏭️ Comment detection OFF for {post.user.email}. Running normal posting code instead.")
                check_scheduled_posts.delay(user_id=post.user_id)
                handled_posting_users.add(post.user_id)