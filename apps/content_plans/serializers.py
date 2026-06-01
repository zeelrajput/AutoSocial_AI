from django.conf import settings
from rest_framework import serializers

from apps.posts.models import Post
from apps.content_plans.models import ContentPlan, ContentPlanItem, UserAIKey


VALID_PLATFORMS = {code for code, _ in Post.PLATFORM_CHOICES}


class ContentPlanItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ContentPlanItem
        fields = [
            "id", "sequence", "platform", "topic", "caption", "hashtags",
            "image", "image_prompt", "scheduled_time", "status",
            "caption_regen_count", "image_regen_count", "error_message",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "sequence", "platform", "image", "image_prompt",
            "caption_regen_count", "image_regen_count", "error_message",
            "created_at", "updated_at",
        ]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class ContentPlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentPlan
        fields = [
            "id", "website_url", "duration_days", "frequency", "custom_interval_days",
            "platforms", "start_date", "posting_time", "total_posts",
            "status", "progress", "error_message", "created_at", "updated_at",
        ]


class ContentPlanDetailSerializer(serializers.ModelSerializer):
    items = ContentPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = ContentPlan
        fields = [
            "id", "website_url", "duration_days", "frequency", "custom_interval_days",
            "platforms", "start_date", "posting_time", "brand_summary",
            "brand_keywords", "total_posts", "status", "progress",
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
        fields = ["configured", "last4", "validated_at"]

    def get_configured(self, obj):
        return bool(obj and obj.gemini_key_encrypted)
