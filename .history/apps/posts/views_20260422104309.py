from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.posts.models import Post
from apps.accounts.models import User
import json

# Create your views here.

@csrf_exempt
def create_post(request):
    if request.method != 'POST':
        return JsonResponse({"message": "only POST allowed"})

    try:
        user_id = request.POST.get('user_id')
        caption = request.POST.get('caption')
        platform = request.POST.get('platform')
        scheduled_time = request.POST.get('scheduled_time')
        media = request.FILES.get('media')   # optional

        user = User.objects.get(id=user_id)

        # only require image for instagram if needed
        if platform == 'instagram' and not media:
            return JsonResponse({"error": "media is required for instagram post"})

        post = Post.objects.create(
            user=user,
            caption=caption,
            platform=platform,
            scheduled_time=scheduled_time,
            media=media
        )

        return JsonResponse({
            "message": "post created successfully",
            "post_id": post.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)})
    
def list_posts(request):
    posts = Post.objects.all().values()
    return JsonResponse(list(posts),safe=False)
