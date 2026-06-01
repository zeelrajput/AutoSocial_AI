"""
Celery tasks for the content plan workflow.

`generate_content_plan` runs the heavy bulk caption generation in the
background so the create-plan API call returns immediately. Images are
generated *on demand* once a caption is approved -- not here.
"""
from celery import shared_task
from django.db import transaction
from django.utils import timezone

# pyrefly: ignore [missing-import]
from apps.content_plans.models import ContentPlan, ContentPlanItem
from apps.content_plans.services import brand_summary as brand_svc
from apps.content_plans.services import captions as captions_svc
from apps.content_plans.services import images as images_svc
from apps.content_plans.services import schedule as schedule_svc
from apps.content_plans.services import scraper as scraper_svc
from apps.content_plans.services.zettalgor import ZettalgorError


def _set_plan_status(plan, status, **fields):
    plan.status = status
    update_fields = ["status", "updated_at"]
    for k, v in fields.items():
        setattr(plan, k, v)
        update_fields.append(k)
    plan.save(update_fields=update_fields)


@shared_task(bind=True, name="apps.content_plans.tasks.generate_content_plan")
def generate_content_plan(self, plan_id: int):
    """Scrape website, summarise brand, generate one caption per slot×platform."""
    try:
        plan = ContentPlan.objects.get(id=plan_id)
    except ContentPlan.DoesNotExist:
        return f"Plan {plan_id} missing"

    _set_plan_status(plan, "generating", progress=0, error_message="")

    try:
        snapshot = scraper_svc.fetch(plan.website_url)
    except Exception as exc:
        _set_plan_status(plan, "failed", error_message=f"Scrape failed: {exc}")
        raise

    slot_count = schedule_svc.slots_per_platform(plan)

    try:
        brand = brand_svc.summarise(snapshot, slot_count)
    except Exception as exc:
        _set_plan_status(plan, "failed", error_message=f"Brand summary failed: {exc}")
        raise

    plan.brand_summary = brand.get("summary", "")
    plan.brand_keywords = brand.get("keywords", [])
    plan.save(update_fields=["brand_summary", "brand_keywords", "updated_at"])

    topics = brand.get("topics", [])
    slot_times = schedule_svc.build(plan)  # may be empty if start_date/time not set yet

    # Create one item per (slot, platform)
    items = []
    for slot_idx in range(slot_count):
        topic = topics[slot_idx] if slot_idx < len(topics) else f"Post {slot_idx+1}"
        scheduled_at = slot_times[slot_idx] if slot_idx < len(slot_times) else None
        for platform in plan.platforms:
            item = ContentPlanItem.objects.create(
                plan=plan,
                sequence=slot_idx + 1,
                platform=platform,
                topic=topic,
                scheduled_time=scheduled_at,
                status="pending_review",
            )
            items.append(item)

    plan.total_posts = len(items)
    plan.save(update_fields=["total_posts", "updated_at"])

    # Generate captions
    total = len(items) or 1
    done = 0
    for item in items:
        try:
            cap = captions_svc.generate(item.topic, item.platform, plan.brand_summary)
            item.caption = cap.get("caption", "")
            item.hashtags = cap.get("hashtags", "")
            item.status = "pending_review"
        except ZettalgorError as exc:
            item.status = "failed"
            item.error_message = str(exc)
        except Exception as exc:
            item.status = "failed"
            item.error_message = f"Caption generation error: {exc}"
        item.save(update_fields=[
            "caption", "hashtags", "status", "error_message", "updated_at"
        ])
        done += 1
        plan.progress = int(done / total * 100)
        plan.save(update_fields=["progress", "updated_at"])

    _set_plan_status(plan, "pending_review", progress=100)
    return f"Generated {len(items)} items for plan {plan_id}"


@shared_task(name="apps.content_plans.tasks.regenerate_caption")
def regenerate_caption(item_id: int):
    """Re-run the caption call on a single item."""
    try:
        item = ContentPlanItem.objects.select_related("plan").get(id=item_id)
    except ContentPlanItem.DoesNotExist:
        return

    item.status = "pending_review"
    item.error_message = ""
    item.save(update_fields=["status", "error_message", "updated_at"])

    try:
        cap = captions_svc.generate(item.topic, item.platform, item.plan.brand_summary)
        item.caption = cap.get("caption", "")
        item.hashtags = cap.get("hashtags", "")
        item.caption_regen_count = (item.caption_regen_count or 0) + 1
        item.save(update_fields=[
            "caption", "hashtags", "caption_regen_count", "updated_at"
        ])
    except Exception as exc:
        item.status = "failed"
        item.error_message = f"Caption regeneration error: {exc}"
        item.save(update_fields=["status", "error_message", "updated_at"])


@shared_task(name="apps.content_plans.tasks.generate_image_for_item")
def generate_image_for_item(item_id: int, prompt_override: str = ""):
    """Generate (or regenerate) the image for a single item."""
    try:
        item = ContentPlanItem.objects.select_related("plan", "plan__user").get(id=item_id)
    except ContentPlanItem.DoesNotExist:
        return

    item.status = "image_generating"
    item.error_message = ""
    item.save(update_fields=["status", "error_message", "updated_at"])

    try:
        saved_path = images_svc.generate(
            item, brand_summary=item.plan.brand_summary, prompt_override=prompt_override
        )
        item.image.name = saved_path
        item.status = "image_pending_review"
        if prompt_override:
            item.image_regen_count = (item.image_regen_count or 0) + 1
        item.save(update_fields=[
            "image", "image_prompt", "image_regen_count", "status", "updated_at"
        ])
    except Exception as exc:
        item.status = "failed"
        item.error_message = f"Image generation error: {exc}"
        item.save(update_fields=["status", "error_message", "updated_at"])
