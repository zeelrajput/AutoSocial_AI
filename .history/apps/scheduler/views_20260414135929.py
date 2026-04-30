from django.shortcuts import render
from django.utils import timezone
from apps.posts.models import Post
from django.http import JsonResponse
from automation_engine.executor.task_runner import run_task
# Create your views here.

def run_schedular(request):
    now = timezone.now()

    pending_posts = Post.objects.filter(
        status = 'pending',
        scheduled_time__lte = now
    )

    processed_ids = []

    for post in pending_posts:
        result = run_task(post.id)

        if result["success"]:
            processed_ids.append(post.id)
        else:
            post.status = 'failed'
            post.error_message = result.get("message", "")
            post.save()

    return JsonResponse({"message":"scheduler executed successfully","processed_post_ids": })