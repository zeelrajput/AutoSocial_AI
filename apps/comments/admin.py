from django.contrib import admin
from .models import PostComment, CommentSettings

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "platform",
        "comment_author",
        "status",
        "reply_type",
        "created_at",
    )
    search_fields = (
        "comment_author",
        "comment_text",
        "reply_text",
    )
    list_filter = (
        "platform",
        "status",
        "reply_type",
    )
    readonly_fields = (
        "comment_hash",
        "created_at",
        "replied_at",
    )

@admin.register(CommentSettings)
class CommentSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "mode", "tone", "is_comment_detection_on")
    list_editable = ("is_comment_detection_on",)
    search_fields = ("user__email",)