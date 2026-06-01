"""
Models for the AI-driven content planning workflow.

A ContentPlan is a bulk request from the user: "give me N days of content
for this website on these platforms". The pipeline then produces one
ContentPlanItem per (slot, platform), each of which holds an AI-generated
caption, hashtags, and (after the user approves the caption) an AI image.

UserAIKey stores per-user encrypted Gemini API keys used for image generation.
"""

from django.conf import settings
from django.db import models

# pyrefly: ignore [missing-import]
from apps.posts.models import Post


PLATFORM_CHOICES = Post.PLATFORM_CHOICES


class ContentPlan(models.Model):
    """Top-level bulk content plan owned by a user."""

    FREQUENCY_CHOICES = (
        ("daily", "Daily"),
        ("alternate", "Alternate days"),
        ("custom", "Custom interval"),
    )

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("generating", "Generating captions"),
        ("pending_review", "Pending review"),
        ("approved", "Approved"),
        ("scheduled", "Scheduled"),
        ("failed", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="content_plans",
    )

    # Step 1 inputs
    website_url = models.URLField(max_length=500)
    duration_days = models.PositiveSmallIntegerField()
    platforms = models.JSONField(default=list)  # list of platform codes

    # Step 6 inputs (can be set later before approve)
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default="daily"
    )
    custom_interval_days = models.PositiveSmallIntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    posting_time = models.TimeField(null=True, blank=True)

    # Generation outputs
    brand_summary = models.TextField(blank=True, default="")
    brand_keywords = models.JSONField(default=list, blank=True)
    total_posts = models.PositiveIntegerField(default=0)

    # Lifecycle
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft"
    )
    progress = models.PositiveSmallIntegerField(default=0)  # 0..100
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan #{self.pk} ({self.website_url}, {self.duration_days}d)"


class ContentPlanItem(models.Model):
    """A single generated draft post inside a plan."""

    STATUS_CHOICES = (
        ("pending_review", "Pending review"),
        ("caption_approved", "Caption approved"),
        ("image_generating", "Image generating"),
        ("image_pending_review", "Image pending review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("scheduled", "Scheduled"),
        ("failed", "Failed"),
    )

    plan = models.ForeignKey(
        ContentPlan,
        on_delete=models.CASCADE,
        related_name="items",
    )
    sequence = models.PositiveSmallIntegerField()
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    topic = models.CharField(max_length=255, blank=True, default="")
    caption = models.TextField(blank=True, default="")
    hashtags = models.TextField(blank=True, default="")
    image = models.FileField(upload_to="content_plans/", blank=True, null=True)
    image_prompt = models.TextField(blank=True, default="")

    scheduled_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=24, choices=STATUS_CHOICES, default="pending_review"
    )

    post = models.OneToOneField(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_plan_item",
    )

    caption_regen_count = models.PositiveSmallIntegerField(default=0)
    image_regen_count = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["plan_id", "sequence", "platform"]

    def __str__(self):
        return f"Item #{self.pk} (plan {self.plan_id}, seq {self.sequence}, {self.platform})"


class UserAIKey(models.Model):
    """Encrypted per-user storage for third-party AI API keys."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_key",
    )

    gemini_key_encrypted = models.BinaryField(blank=True, null=True)
    gemini_key_last4 = models.CharField(max_length=4, blank=True, default="")
    gemini_validated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI keys for {self.user_id}"
