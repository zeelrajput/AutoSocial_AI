import hashlib

from .models import PostComment, CommentSettings
from .ai_reply import generate_ai_reply


def create_comment_if_new(post, platform, author, text):

    raw = f"{post.id}_{platform}_{author}_{text}"

    comment_hash = hashlib.sha256(
        raw.encode()
    ).hexdigest()

    # Check if this comment already exists
    try:
        existing = PostComment.objects.get(comment_hash=comment_hash)
        # If it was already replied to successfully, or explicitly ignored, skip it
        if existing.status in ["replied", "reply_sent", "ignored"]:
            return None
        # If it's still pending, return it so the system retries the reply
        print(f"🔄 Retrying pending reply for comment by {author}")
        return existing
    except PostComment.DoesNotExist:
        pass  # Brand new comment, proceed to create

    # Fetch user settings
    settings, _ = CommentSettings.objects.get_or_create(user=post.user)

    # Fetch previous comments for context
    previous_comments_qs = PostComment.objects.filter(post=post).order_by('-created_at')[:5]
    prev_comments_list = []
    for c in reversed(previous_comments_qs): # Chronological order
        prev_comments_list.append(f"{c.comment_author}: {c.comment_text}")
        if c.reply_text and c.status == "replied":
            prev_comments_list.append(f"Bot (You): {c.reply_text}")
            
    prev_comments_str = "\n".join(prev_comments_list)

    # Call AI generation with the new schema and settings
    ai_result = generate_ai_reply(
        comment_text=text,
        author=author,
        post_caption=post.caption,
        previous_comments=prev_comments_str,
        platform=platform,
        mode=settings.mode,
        tone=settings.tone,
        keyword_replies=settings.keyword_replies,
        default_reply=settings.default_reply
    )

    should_reply = ai_result.get("should_reply", True)
    reply_text = ai_result.get("reply", "")
    
    # Strip non-BMP characters (emojis) so ChromeDriver can type it safely
    if reply_text:
        reply_text = "".join(c for c in reply_text if ord(c) <= 0xFFFF)

    reply_type = "predefined" if ai_result.get("used_predefined") else "ai"
    
    # Determine the status to save
    status = "reply_pending" if should_reply and reply_text else "ignored"

    comment = PostComment.objects.create(
        user=post.user,
        post=post,
        platform=platform,
        comment_author=author,
        comment_text=text,
        comment_hash=comment_hash,
        reply_type=reply_type,
        reply_text=reply_text,
        status=status
    )

    # Return None if it was ignored so we don't try to send a reply task to the agent
    if status == "ignored":
        print(f"⏭️ Comment by {author} ignored by AI (Type: {ai_result.get('type')})")
        return None

    return comment