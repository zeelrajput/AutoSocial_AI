from django.contrib import admin
from apps.accounts.models import *
from django.contrib.auth.admin import UserAdmin,Agent

admin.site.register(User, UserAdmin)

@admin.register(AgentDevice)
class AgentDeviceAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "device_name", "is_online", "is_active", "created_at"]
    readonly_fields = ["raw_token", "token_hash", "is_online", "last_seen", "created_at"]