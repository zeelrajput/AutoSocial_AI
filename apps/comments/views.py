from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def test_comments(request):
    return JsonResponse({
        "success": True,
        "message": "Comments app working"
    })


from django.http import JsonResponse
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# pyrefly: ignore [missing-import]
from apps.posts.models import Post
from .models import PostComment, CommentSettings
from .ai_reply import generate_ai_reply

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_reply_api(request):
    try:
        data = request.data

        post_id = data.get("post_id")
        mode = data.get("mode", "AI").upper()

        if mode not in ["AI", "MANUAL"]:
            return JsonResponse({
                "success": False,
                "message": "mode must be AI or MANUAL"
            }, status=400)

        if not post_id:
            return JsonResponse({
                "success": False,
                "message": "post_id required"
            }, status=400)

        post = Post.objects.get(id=post_id)

        comment = PostComment.objects.filter(
            post=post,
            status="new",
            reply_text__isnull=True,
        ).order_by("-created_at").first()

        if not comment:
            return JsonResponse({
                "success": False,
                "message": "No comments found on this post"
            }, status=404)

        settings, _ = CommentSettings.objects.get_or_create(
            user=post.user
        )

        result = generate_ai_reply(
            comment_text=comment.comment_text,
            author=comment.comment_author,
            post_caption=post.caption,
            previous_comments="",
            platform=post.platform,
            mode=mode,
            tone=settings.tone,
            keyword_replies=settings.keyword_replies,
            default_reply=settings.default_reply
        )

        if not result.get("should_reply"):
            comment.status = "ignored"
            comment.save(update_fields=["status"])

            return JsonResponse({
                "success": True,
                "message": "Comment ignored by AI"
            })

        reply_text = result["reply"]

        comment.reply_text = reply_text
        comment.status = "reply_pending"
        comment.save(update_fields=["reply_text", "status"])

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"agent_{post.user.id}",
            {
                "type": "send_reply_comment",
                "comment_id": comment.id,
                "platform": post.platform,
                "reply_text": reply_text,
                "post_url": post.post_url,
                "author": comment.comment_author,
                "comment_text": comment.comment_text,
            }
        )

        return JsonResponse({
            "success": True,
            "message": "Reply sent to agent",
            "reply": reply_text
        })

    except Post.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Post not found"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)