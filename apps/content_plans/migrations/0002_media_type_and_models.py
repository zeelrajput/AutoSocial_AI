from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content_plans", "0001_initial"),
    ]

    operations = [
        # ContentPlan: media_type + per-plan model overrides
        migrations.AddField(
            model_name="contentplan",
            name="media_type",
            field=models.CharField(
                choices=[("image", "Image"), ("video", "Video")],
                default="image",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="contentplan",
            name="image_model",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="contentplan",
            name="video_model",
            field=models.CharField(blank=True, default="", max_length=64),
        ),

        # ContentPlanItem: media_type override + video fields + regen count
        migrations.AddField(
            model_name="contentplanitem",
            name="media_type",
            field=models.CharField(
                choices=[("image", "Image"), ("video", "Video")],
                default="image",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="contentplanitem",
            name="video",
            field=models.FileField(
                blank=True, null=True, upload_to="content_plans/"
            ),
        ),
        migrations.AddField(
            model_name="contentplanitem",
            name="video_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="contentplanitem",
            name="video_operation",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="contentplanitem",
            name="video_regen_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="contentplanitem",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_review", "Pending review"),
                    ("caption_approved", "Caption approved"),
                    ("image_generating", "Image generating"),
                    ("image_pending_review", "Image pending review"),
                    ("video_generating", "Video generating"),
                    ("video_pending_review", "Video pending review"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("scheduled", "Scheduled"),
                    ("failed", "Failed"),
                ],
                default="pending_review",
                max_length=24,
            ),
        ),

        # UserAIKey: default model preferences
        migrations.AddField(
            model_name="useraikey",
            name="default_image_model",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="useraikey",
            name="default_video_model",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
