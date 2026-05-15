import json
import requests
import re
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# pyrefly: ignore [missing-import]
from apps.posts.models import Post, PostMedia
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_post(request):

    try:
        caption = request.POST.get("caption")
        platform = request.POST.get("platform")
        scheduled_time = request.POST.get("scheduled_time")

        media_files = request.FILES.getlist("media")

        if platform == "instagram" and not media_files:
            return JsonResponse({
                "success": False,
                "message": "Media is required for Instagram post",
                "errors": {}
            }, status=400)

        post = Post.objects.create(
            user=request.user,
            caption=caption,
            platform=platform,
            scheduled_time=scheduled_time,
            status="scheduled"
        )

        for file in media_files:
            PostMedia.objects.create(post=post, file=file)

        return JsonResponse({
            "success": True,
            "message": "Post created successfully",
            "data": {
                "post_id": post.id,
                "user_id": request.user.id,
                "media_count": len(media_files)
            }
        })

    except Exception as e:
        return JsonResponse({
    "success": False,
    "message": "Something went wrong",
    "errors": str(e)
}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_posts(request):

    posts = Post.objects.filter(user=request.user)

    post_data = []

    for post in posts:

        media_urls = []

        for media in post.media_files.all():
            media_urls.append(
                request.build_absolute_uri(media.file.url)
            )

        post_data.append({
            "id": post.id,
            "user_id": post.user.id,
            "caption": post.caption,
            "media": media_urls,
            "platform": post.platform,
            "scheduled_time": post.scheduled_time,
            "status": post.status
        })

    return JsonResponse({
        "success": True,
        "message": "Posts fetched successfully",
        "data": post_data
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_ai_caption(request):
    try:
        if request.content_type and "application/json" in request.content_type:
            body = json.loads(request.body.decode("utf-8"))
            topic = body.get("topic")
            platform = body.get("platform", "instagram")
        else:
            topic = request.POST.get("topic")
            platform = request.POST.get("platform", "instagram")

        if not topic:
            return JsonResponse({
                "success": False,
                "message": "Topic is required",
                "errors": {}
            }, status=400)

        zettalgor_api_url = getattr(settings, "ZETTALGOR_API_URL", "")
        zettalgor_api_key = getattr(settings, "ZETTALGOR_API_KEY", "")
        zettalgor_model = getattr(settings, "ZETTALGOR_MODEL", "ZAI8")

        if not zettalgor_api_url or "PASTE_" in zettalgor_api_url:
            return JsonResponse({
                "success": False,
                "message": "Invalid Zettalgor API URL",
                "errors": {}
            }, status=500)

        prompt = f"""
Generate one social media caption with hashtags.

Platform: {platform}
Topic: {topic}

Return only this format:
Caption: ...
Hashtags: ...
"""

        response = requests.post(
            zettalgor_api_url,
            json={
                "model": zettalgor_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            headers={
                "Authorization": f"Bearer {zettalgor_api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code >= 400:
            return JsonResponse({
                "success": False,
                "message": "Zettalgor API request failed",
                "errors": {
                    "status_code": response.status_code,
                    "details": response.text
                }
            }, status=400)

        data = response.json()

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        # 🔥 CLEANUP
        content = content.replace("\\n", "\n")   # fix \n
        content = content.replace("\\", "")      # remove backslashes
        content = content.replace('"', "")       # remove quotes
        content = content.strip()

        # remove labels
        content = re.sub(r"(?i)caption:\s*", "", content)
        content = re.sub(r"(?i)hashtags:\s*", "", content)

        # split lines
        lines = content.split("\n")

        caption_lines = []
        hashtag_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                hashtag_lines.append(line)
            else:
                caption_lines.append(line)

        caption = " ".join(caption_lines).strip()
        hashtags = " ".join(hashtag_lines).strip()

        return JsonResponse({
            "success": True,
            "message": "Caption generated successfully",
            "data": {
                "caption": caption,
                "hashtags": hashtags
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON payload",
            "errors": {}
        }, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "success": False,
            "message": "API request error",
            "errors": str(e)
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Something went wrong",
            "errors": str(e)
        }, status=400)