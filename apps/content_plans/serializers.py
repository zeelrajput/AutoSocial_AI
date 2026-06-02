from django.conf import settings
from rest_framework import serializers

from apps.posts.models import Post
from apps.content_plans.models import (
    ContentPlan,
    ContentPlanItem,
    UserAIKey,
    GEMINI_IMAGE_MODEL_CHOICES,
    GEMINI_VIDEO_MODEL_CHOICES,
    MEDIA_TYPE_CHOICES,
)


VALID_PLATFORMS = {code for code, _ in Post.PLATFORM_CHOICES}
VALID_IMAGE_MODELS = {code for code, _ in GEMINI_IMAGE_MODEL_CHOICES}
VALID_VIDEO_MODELS = {code for code, _ in GEMINI_VIDEO_MODEL_CHOICES}


def _absolute_file_url(file_field, request):
    if not file_field:
        return None
    url = file_field.url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


class ContentPlanItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = ContentPlanItem
        fields = [
            "id", "sequence", "platform", "topic", "caption", "hashtags",
            "image", "image_prompt", "video", "video_prompt", "media_type",
            "media_url", "scheduled_time", "status",
            "caption_regen_count", "image_regen_count", "video_regen_count",
            "error_message", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "sequence", "platform", "image", "image_prompt",
            "video", "video_prompt", "media_url",
            "caption_regen_count", "image_regen_count", "video_regen_count",
            "error_message", "created_at", "updated_at",
        ]

    def get_image(self, obj):
        return _absolute_file_url(obj.image, self.context.get("request"))

    def get_video(self, obj):
        return _absolute_file_url(obj.video, self.context.get("request"))

    def get_media_url(self, obj):
        request = self.context.get("request")
        if (obj.media_type or "image") == "video" and obj.video:
            return _absolute_file_url(obj.video, request)
        return _absolute_file_url(obj.image, request)


class ContentPlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentPlan
        fields = [
            "id", "website_url", "duration_days", "frequency", "custom_interval_days",
            "platforms", "start_date", "posting_time", "total_posts",
            "media_type", "image_model", "video_model",
            "status", "progress", "error_message", "created_at", "updated_at",
        ]


class ContentPlanDetailSerializer(serializers.ModelSerializer):
    items = ContentPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = ContentPlan
        fields = [
            "id", "website_url", "duration_days", "frequency", "custom_interval_days",
            "platforms", "start_date", "posting_time", "brand_summary",
            "brand_keywords", "total_posts",
            "media_type", "image_model", "video_model",
            "status", "progress",
            "error_message", "created_at", "updated_at", "items",
        ]


class ContentPlanCreateSerializer(serializers.Serializer):
    website_url = serializers.URLField()
    duration_days = serializers.IntegerField()
    platforms = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )
    # frequency / start_date / posting_time can be supplied here OR later in /schedule/
    frequency = serializers.ChoiceField(
        choices=ContentPlan.FREQUENCY_CHOICES, required=False, default="daily"
    )
    custom_interval_days = serializers.IntegerField(required=False, default=1)
    start_date = serializers.DateField(required=False, allow_null=True)
    posting_time = serializers.TimeField(required=False, allow_null=True)

    # New: media type + per-plan model choices
    media_type = serializers.ChoiceField(
        choices=MEDIA_TYPE_CHOICES, required=False, default="image"
    )
    image_model = serializers.CharField(required=False, allow_blank=True, default="")
    video_model = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_image_model(self, value):
        if value and value not in VALID_IMAGE_MODELS:
            raise serializers.ValidationError(
                f"Unknown image_model. Allowed: {sorted(VALID_IMAGE_MODELS)}"
            )
        return value

    def validate_video_model(self, value):
        if value and value not in VALID_VIDEO_MODELS:
            raise serializers.ValidationError(
                f"Unknown video_model. Allowed: {sorted(VALID_VIDEO_MODELS)}"
            )
        return value

    def validate_duration_days(self, value):
        lo = getattr(settings, "CONTENT_PLAN_MIN_DURATION_DAYS", 1)
        hi = getattr(settings, "CONTENT_PLAN_MAX_DURATION_DAYS", 30)
        if value < lo or value > hi:
            raise serializers.ValidationError(
                f"duration_days must be between {lo} and {hi}."
            )
        return value

    def validate_platforms(self, value):
        invalid = [p for p in value if p not in VALID_PLATFORMS]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid platforms: {invalid}. Allowed: {sorted(VALID_PLATFORMS)}"
            )
        # de-dup
        return list(dict.fromkeys(value))

    def validate_custom_interval_days(self, value):
        if value < 1 or value > 30:
            raise serializers.ValidationError("custom_interval_days must be 1..30")
        return value


class ContentPlanScheduleSerializer(serializers.Serializer):
    frequency = serializers.ChoiceField(choices=ContentPlan.FREQUENCY_CHOICES)
    custom_interval_days = serializers.IntegerField(required=False, default=1)
    start_date = serializers.DateField()
    posting_time = serializers.TimeField()

    def validate_custom_interval_days(self, value):
        if value < 1 or value > 30:
            raise serializers.ValidationError("custom_interval_days must be 1..30")
        return value


class UserAIKeySerializer(serializers.ModelSerializer):
    configured = serializers.SerializerMethodField()
    last4 = serializers.CharField(source="gemini_key_last4", read_only=True)
    validated_at = serializers.DateTimeField(source="gemini_validated_at", read_only=True)

    class Meta:
        model = UserAIKey
        fields = [
            "configured", "last4", "validated_at",
            "default_image_model", "default_video_model",
        ]

    def get_configured(self, obj):
        return bool(obj and obj.gemini_key_encrypted)


class UserAIModelDefaultsSerializer(serializers.Serializer):
    """PATCH-only serializer for updating user's default Gemini models."""

    default_image_model = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    default_video_model = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate_default_image_model(self, value):
        if value and value not in VALID_IMAGE_MODELS:
            raise serializers.ValidationError(
                f"Unknown image model. Allowed: {sorted(VALID_IMAGE_MODELS)}"
            )
        return value

    def validate_default_video_model(self, value):
        if value and value not in VALID_VIDEO_MODELS:
            raise serializers.ValidationError(
                f"Unknown video model. Allowed: {sorted(VALID_VIDEO_MODELS)}"
            )
        return value


class GeminiModelsSerializer(serializers.Serializer):
    """Static list of supported Gemini models for the UI to render dropdowns."""

    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    def get_image(self, _):
        return [{"value": v, "label": l} for v, l in GEMINI_IMAGE_MODEL_CHOICES]

    def get_video(self, _):
        return [{"value": v, "label": l} for v, l in GEMINI_VIDEO_MODEL_CHOICES]
