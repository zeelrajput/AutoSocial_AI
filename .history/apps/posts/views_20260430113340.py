from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from apps.posts.models import Post, PostMedia


@csrf_exempt
@login_required
def create_post(request):
    if request.method != "POST":
        return JsonResponse({"message": "only POST allowed"}, status=405)

    try:
        caption = request.POST.get("caption")
        platform = request.POST.get("platform")
        scheduled_time = request.POST.get("scheduled_time")

        # ✅ get multiple files
        media_files = request.FILES.getlist("media")

        # Instagram must have at least 1 image
        if platform == "instagram" and not media_files:
            return JsonResponse(
                {"error": "media is required for instagram post"},
                status=400
            )

        # create post (no single media now)
        post = Post.objects.create(
            user=request.user,
            caption=caption,
            platform=platform,
            scheduled_time=scheduled_time,
            status="pending"
        )

        # save multiple media
        for file in media_files:
            PostMedia.objects.create(post=post, file=file)
            

        return JsonResponse({
            "message": "post created successfully",
            "post_id": post.id,
            "user_id": request.user.id,
            "media_count": len(media_files)
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@login_required
def list_posts(request):
    posts = Post.objects.filter(user=request.user).values()
    return JsonResponse(list(posts), safe=False)