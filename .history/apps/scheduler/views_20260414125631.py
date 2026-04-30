from django.shortcuts import render
from django.utils import timezone
from apps.posts.models import Post
from django.http import JsonResponse
# Create your views here.

def run_schedular(request):
    now = timezone.now()

    pending_posts = Post.objects.filter(
        status = 'pending',
        scheduled_time_lte = now
    )

    updated_posts = []

    for post in pending_posts:
        post.status = 'scheduled'
        post.save()
        updated_posts.append(post.id)

    return JsonResponse({"messge":"scheduler executed successfully",""})