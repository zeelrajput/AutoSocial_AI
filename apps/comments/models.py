from django.db import models
# pyrefly: ignore [missing-import]
from apps.posts.models import Post
# pyrefly: ignore [missing-import]
from apps.accounts.models import User


class PostComment(models.Model):

    REPLY_TYPE_CHOICES = (
        ("predefined", "Predefined"),
        ("ai", "AI"),
    )

    STATUS_CHOICES = (
        ("new", "New"),
        ("reply_pending", "Reply Pending"),
        ("reply_sent", "Reply Sent"),
        ("reply_failed", "Reply Failed"),
        ("ignored", "Ignored"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    platform = models.CharField(max_length=50)

    comment_author = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    comment_text = models.TextField()

    comment_hash = models.CharField(
        max_length=255,
        unique=True
    )

    reply_type = models.CharField(
        max_length=20,
        choices=REPLY_TYPE_CHOICES,
        default="predefined"
    )

    reply_text = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="new"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    replied_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.platform} - {self.comment_author}"


class CommentSettings(models.Model):
    MODE_CHOICES = (
        ("AI", "AI Mode"),
        ("MANUAL", "Manual Mode"),
    )

    TONE_CHOICES = (
        ("friendly", "Friendly"),
        ("professional", "Professional"),
        ("casual", "Casual"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="comment_settings"
    )

    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default="AI"
    )

    tone = models.CharField(
        max_length=20,
        choices=TONE_CHOICES,
        default="friendly"
    )

    keyword_replies = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON mapping of keywords to replies"
    )

    default_reply = models.TextField(
        default="Thank you for your comment!",
        blank=True
    )

    is_comment_detection_on = models.BooleanField(
        default=True,
        help_text="If enabled, it runs comment detection."
    )

    def __str__(self):
        return f"Settings for {self.user.email}"