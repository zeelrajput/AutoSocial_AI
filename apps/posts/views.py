import json
import requests
import re
from django.conf import settings
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

        media_files = request.FILES.getlist("media")

        if platform == "instagram" and not media_files:
            return JsonResponse(
                {"error": "media is required for instagram post"},
                status=400
            )

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


@csrf_exempt
@login_required
def generate_ai_caption(request):
    if request.method != "POST":
        return JsonResponse({"message": "only POST allowed"}, status=405)

    try:
        if request.content_type and "application/json" in request.content_type:
            body = json.loads(request.body.decode("utf-8"))
            topic = body.get("topic")
            platform = body.get("platform", "instagram")
        else:
            topic = request.POST.get("topic")
            platform = request.POST.get("platform", "instagram")

        if not topic:
            return JsonResponse({"error": "topic is required"}, status=400)

        zettalgor_api_url = getattr(settings, "ZETTALGOR_API_URL", "")
        zettalgor_api_key = getattr(settings, "ZETTALGOR_API_KEY", "")
        zettalgor_model = getattr(settings, "ZETTALGOR_MODEL", "ZAI8")

        if not zettalgor_api_url or "PASTE_" in zettalgor_api_url:
            return JsonResponse({
                "error": "Please add real Chat Completions endpoint in ZETTALGOR_API_URL"
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
                "error": "Zettalgor API request failed",
                "status_code": response.status_code,
                "details": response.text
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
            "message": "caption generated successfully",
            "caption": caption,
            "hashtags": hashtags,
            "raw_response": data
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"API request error: {str(e)}"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)