import hashlib

from .models import PostComment, CommentSettings
from .ai_reply import generate_ai_reply


def create_comment_if_new(post, platform, author, text):

    print("🔥 FUNCTION CALLED")
    print("POST ID:", post.id)
    print("AUTHOR:", author)
    print("TEXT:", text)

    raw = f"{post.id}_{platform}_{author}_{text}"

    comment_hash = hashlib.sha256(
        raw.encode()
    ).hexdigest()

    try:
        existing = PostComment.objects.get(comment_hash=comment_hash)

        if existing.status in ["replied", "reply_sent", "ignored"]:
            return None

        print(f"🔄 Retrying pending reply for comment by {author}")
        return existing

    except PostComment.DoesNotExist:
        pass

    print("💾 SAVING COMMENT...")

    comment = PostComment.objects.create(
        user=post.user,
        post=post,
        platform=platform,
        comment_id=f"{post.id}_{author}_{comment_hash[:10]}",
        comment_author=author,
        comment_text=text,
        comment_hash=comment_hash,
        reply_type="ai",
        status="new"
    )

    print("✅ COMMENT SAVED:", comment.id)

    return comment