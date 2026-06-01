from django.contrib import admin

from .models import ContentPlan, ContentPlanItem, UserAIKey


@admin.register(ContentPlan)
class ContentPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "website_url", "duration_days", "frequency",
                    "status", "progress", "total_posts", "created_at")
    list_filter = ("status", "frequency")
    search_fields = ("website_url", "user__email")


@admin.register(ContentPlanItem)
class ContentPlanItemAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "sequence", "platform", "status",
                    "scheduled_time", "caption_regen_count", "image_regen_count")
    list_filter = ("status", "platform")


@admin.register(UserAIKey)
class UserAIKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gemini_key_last4", "gemini_validated_at",
                    "created_at")
    readonly_fields = ("gemini_key_encrypted",)
