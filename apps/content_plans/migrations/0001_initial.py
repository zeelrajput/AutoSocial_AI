from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("posts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("website_url", models.URLField(max_length=500)),
                ("duration_days", models.PositiveSmallIntegerField()),
                ("platforms", models.JSONField(default=list)),
                ("frequency", models.CharField(choices=[("daily","Daily"),("alternate","Alternate days"),("custom","Custom interval")], default="daily", max_length=20)),
                ("custom_interval_days", models.PositiveSmallIntegerField(default=1)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("posting_time", models.TimeField(blank=True, null=True)),
                ("brand_summary", models.TextField(blank=True, default="")),
                ("brand_keywords", models.JSONField(blank=True, default=list)),
                ("total_posts", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("draft","Draft"),("generating","Generating captions"),("pending_review","Pending review"),("approved","Approved"),("scheduled","Scheduled"),("failed","Failed")], default="draft", max_length=20)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="content_plans", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ContentPlanItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.PositiveSmallIntegerField()),
                ("platform", models.CharField(choices=[("facebook","Facebook"),("instagram","Instagram"),("linkedin","Linkedin"),("x","X")], max_length=20)),
                ("topic", models.CharField(blank=True, default="", max_length=255)),
                ("caption", models.TextField(blank=True, default="")),
                ("hashtags", models.TextField(blank=True, default="")),
                ("image", models.FileField(blank=True, null=True, upload_to="content_plans/")),
                ("image_prompt", models.TextField(blank=True, default="")),
                ("scheduled_time", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("pending_review","Pending review"),("caption_approved","Caption approved"),("image_generating","Image generating"),("image_pending_review","Image pending review"),("approved","Approved"),("rejected","Rejected"),("scheduled","Scheduled"),("failed","Failed")], default="pending_review", max_length=24)),
                ("caption_regen_count", models.PositiveSmallIntegerField(default=0)),
                ("image_regen_count", models.PositiveSmallIntegerField(default=0)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="content_plans.contentplan")),
                ("post", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_plan_item", to="posts.post")),
            ],
            options={"ordering": ["plan_id", "sequence", "platform"]},
        ),
        migrations.CreateModel(
            name="UserAIKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("gemini_key_encrypted", models.BinaryField(blank=True, null=True)),
                ("gemini_key_last4", models.CharField(blank=True, default="", max_length=4)),
                ("gemini_validated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="ai_key", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
