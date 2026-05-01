from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from apps.posts.models import Post


@csrf_exempt
@login_required
def create_post(request):
    if request.method != "POST":
        return JsonResponse({"message": "only POST allowed"}, status=405)

    try:
        caption = request.POST.get("caption")
        platform = request.POST.get("platform")
        scheduled_time = request.POST.get("scheduled_time")
        media = request.FILES.get("media")

        if platform == "instagram" and not media:
            return JsonResponse({"error": "media is required for instagram post"}, status=400)

        post = Post.objects.create(
            user=request.user,   # ✅ logged-in user
            caption=caption,
            platform=platform,
            scheduled_time=scheduled_time,
            media=media,
            status="pending"
        )

        return JsonResponse({
            "message": "post created successfully",
            "post_id": post.id,
            "user_id": request.user.id
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def list_posts(request):
    posts = Post.objects.filter(user=request.user).values()
    return JsonResponse(list(posts), safe=False)