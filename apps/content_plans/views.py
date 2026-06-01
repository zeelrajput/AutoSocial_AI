"""
REST API views for the AI content-planning workflow.

URL prefix: ``/api/`` (mounted from config.urls)

Endpoints
---------
Gemini key management:
    GET/POST/DELETE   /api/ai-keys/gemini/

Content plans:
    POST              /api/content-plans/
    GET               /api/content-plans/
    GET               /api/content-plans/<id>/
    GET               /api/content-plans/<id>/progress/
    DELETE            /api/content-plans/<id>/
    POST              /api/content-plans/<id>/schedule/
    POST              /api/content-plans/<id>/approve/

Item review / regeneration:
    PATCH             /api/content-plans/items/<item_id>/
    POST              /api/content-plans/items/<item_id>/regenerate-caption/
    POST              /api/content-plans/items/<item_id>/approve-caption/
    POST              /api/content-plans/items/<item_id>/regenerate-image/
    POST              /api/content-plans/items/<item_id>/upload-image/
    POST              /api/content-plans/items/<item_id>/approve-image/
    POST              /api/content-plans/items/<item_id>/reject/
"""
import math

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.posts.models import Post, PostMedia
from apps.content_plans.crypto import encrypt
from apps.content_plans.models import ContentPlan, ContentPlanItem, UserAIKey
from apps.content_plans.serializers import (
    ContentPlanCreateSerializer,
    ContentPlanDetailSerializer,
    ContentPlanListSerializer,
    ContentPlanItemSerializer,
    ContentPlanScheduleSerializer,
    UserAIKeySerializer,
)
from apps.content_plans.services import images as images_svc
from apps.content_plans.services import schedule as schedule_svc
from apps.content_plans.tasks import (
    generate_content_plan,
    generate_image_for_item,
    regenerate_caption,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data=None, message="OK", http=200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=http)


def _err(message, errors=None, http=400):
    return Response(
        {"success": False, "message": message, "errors": errors or {}},
        status=http,
    )


def _get_plan_for_user(user, plan_id):
    return get_object_or_404(ContentPlan, id=plan_id, user=user)


def _get_item_for_user(user, item_id):
    return get_object_or_404(ContentPlanItem, id=item_id, plan__user=user)


# ---------------------------------------------------------------------------
# Gemini API key management
# ---------------------------------------------------------------------------

@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def gemini_key(request):
    if request.method == "GET":
        record = UserAIKey.objects.filter(user=request.user).first()
        if not record:
            return _ok({"configured": False, "last4": "", "validated_at": None})
        return _ok(UserAIKeySerializer(record).data)

    if request.method == "DELETE":
        UserAIKey.objects.filter(user=request.user).delete()
        return _ok(message="Gemini key removed")

    # POST
    api_key = (request.data.get("api_key") or "").strip()
    if not api_key:
        return _err("api_key is required")

    # Light validation against Gemini (best-effort).
    try:
        valid = images_svc.validate_api_key(api_key)
    except Exception:
        valid = False

    record, _ = UserAIKey.objects.get_or_create(user=request.user)
    record.gemini_key_encrypted = encrypt(api_key)
    record.gemini_key_last4 = api_key[-4:]
    record.gemini_validated_at = timezone.now() if valid else None
    record.save()

    data = UserAIKeySerializer(record).data
    data["validated"] = bool(valid)
    return _ok(data, message="Gemini key saved")


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def plans_collection(request):
    if request.method == "GET":
        qs = ContentPlan.objects.filter(user=request.user)
        return _ok(ContentPlanListSerializer(qs, many=True).data)

    serializer = ContentPlanCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return _err("Invalid plan input", serializer.errors)

    # Require a Gemini key on file (image generation will need it).
    record = UserAIKey.objects.filter(user=request.user).first()
    if not record or not record.gemini_key_encrypted:
        return _err(
            "Add your Gemini API key before creating a content plan.",
            errors={"gemini_api_key": "missing"},
            http=400,
        )

    # Reject if user already has a plan currently generating.
    if ContentPlan.objects.filter(user=request.user, status="generating").exists():
        return _err(
            "Another plan is currently generating. Please wait for it to finish.",
            http=409,
        )

    data = serializer.validated_data
    plan = ContentPlan.objects.create(
        user=request.user,
        website_url=data["website_url"],
        duration_days=data["duration_days"],
        platforms=data["platforms"],
        frequency=data.get("frequency") or "daily",
        custom_interval_days=data.get("custom_interval_days") or 1,
        start_date=data.get("start_date"),
        posting_time=data.get("posting_time"),
        status="generating",
    )

    # Pre-compute total_posts for UI even before generation finishes.
    slots = schedule_svc.slots_per_platform(plan)
    plan.total_posts = slots * max(1, len(plan.platforms))
    plan.save(update_fields=["total_posts"])

    # Kick off async generation. .delay if Celery available; eager fallback.
    try:
        generate_content_plan.delay(plan.id)
    except Exception:
        generate_content_plan(plan.id)

    return _ok(
        {"plan_id": plan.id, "total_posts": plan.total_posts, "status": plan.status},
        message="Plan created and generation started",
        http=201,
    )


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def plan_detail(request, plan_id: int):
    plan = _get_plan_for_user(request.user, plan_id)

    if request.method == "DELETE":
        if plan.status not in {"draft", "pending_review", "failed", "approved"}:
            return _err(
                f"Cannot delete a plan in status '{plan.status}'.", http=409
            )
        plan.delete()
        return _ok(message="Plan deleted")

    return _ok(ContentPlanDetailSerializer(plan, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_progress(request, plan_id: int):
    plan = _get_plan_for_user(request.user, plan_id)
    completed = plan.items.exclude(status__in=["pending_review", "failed"]).count()
    return _ok({
        "plan_id": plan.id,
        "status": plan.status,
        "progress": plan.progress,
        "completed_items": completed,
        "total_posts": plan.total_posts,
        "error_message": plan.error_message,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def plan_schedule(request, plan_id: int):
    plan = _get_plan_for_user(request.user, plan_id)
    if plan.status not in {"pending_review", "approved"}:
        return _err(
            f"Cannot schedule a plan in status '{plan.status}'.", http=409
        )

    serializer = ContentPlanScheduleSerializer(data=request.data)
    if not serializer.is_valid():
        return _err("Invalid schedule input", serializer.errors)

    today = timezone.localdate()
    if serializer.validated_data["start_date"] < today:
        return _err("start_date cannot be in the past")

    data = serializer.validated_data
    plan.frequency = data["frequency"]
    plan.custom_interval_days = data.get("custom_interval_days") or 1
    plan.start_date = data["start_date"]
    plan.posting_time = data["posting_time"]
    plan.save(update_fields=[
        "frequency", "custom_interval_days", "start_date", "posting_time", "updated_at"
    ])

    # Re-spread items across the new schedule.
    slot_times = schedule_svc.build(plan)
    if slot_times:
        items_by_seq = {}
        for item in plan.items.all().order_by("sequence", "id"):
            items_by_seq.setdefault(item.sequence, []).append(item)
        for seq, item_list in items_by_seq.items():
            idx = seq - 1
            if 0 <= idx < len(slot_times):
                for it in item_list:
                    it.scheduled_time = slot_times[idx]
                    it.save(update_fields=["scheduled_time", "updated_at"])

    return _ok(
        ContentPlanDetailSerializer(plan, context={"request": request}).data,
        message="Schedule saved",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def plan_approve(request, plan_id: int):
    plan = _get_plan_for_user(request.user, plan_id)

    # Idempotency
    if plan.status == "scheduled":
        post_ids = list(
            plan.items.filter(post__isnull=False).values_list("post_id", flat=True)
        )
        return _ok(
            {"scheduled_count": len(post_ids), "post_ids": post_ids},
            message="Plan already scheduled",
        )

    if not plan.start_date or not plan.posting_time:
        return _err(
            "Set start_date and posting_time via /schedule/ before approving.",
            http=400,
        )

    eligible = plan.items.filter(status="approved")
    if not eligible.exists():
        return _err("No approved items to schedule.", http=400)

    missing_image = list(eligible.filter(image="").values_list("id", flat=True))
    if missing_image:
        return _err(
            "Some approved items have no image yet.",
            errors={"items_without_image": missing_image},
            http=400,
        )

    now = timezone.now()
    post_ids = []
    with transaction.atomic():
        for item in eligible.select_for_update():
            if not item.scheduled_time or item.scheduled_time < now:
                # Skip past-due rows
                continue
            caption_text = item.caption.strip()
            if item.hashtags.strip():
                caption_text = f"{caption_text}\n\n{item.hashtags.strip()}"

            post = Post(
                user=plan.user,
                caption=caption_text,
                platform=item.platform,
                scheduled_time=item.scheduled_time,
                status="scheduled",
            )
            if item.image:
                # Reuse the already-saved image file (no re-upload).
                post.media.name = item.image.name
            post.save()
            if item.image:
                PostMedia.objects.create(post=post, file=item.image.name)

            item.post = post
            item.status = "scheduled"
            item.save(update_fields=["post", "status", "updated_at"])
            post_ids.append(post.id)

        plan.status = "scheduled"
        plan.save(update_fields=["status", "updated_at"])

    return _ok(
        {"scheduled_count": len(post_ids), "post_ids": post_ids},
        message="Plan scheduled",
    )


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def item_update(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    if item.plan.status not in {"pending_review", "approved"}:
        return _err(
            f"Plan status '{item.plan.status}' does not allow edits.", http=409
        )

    updated = []
    for field in ("caption", "hashtags"):
        if field in request.data:
            setattr(item, field, request.data[field])
            updated.append(field)
    if "scheduled_time" in request.data:
        item.scheduled_time = request.data["scheduled_time"]
        updated.append("scheduled_time")

    if updated:
        updated.append("updated_at")
        item.save(update_fields=updated)

    return _ok(ContentPlanItemSerializer(item, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def item_regenerate_caption(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    max_regens = getattr(settings, "CONTENT_PLAN_MAX_REGENS", 3)
    if item.caption_regen_count >= max_regens:
        return _err(
            f"Caption regeneration limit reached ({max_regens}).", http=429
        )
    if "topic" in request.data and request.data["topic"]:
        item.topic = request.data["topic"]
        item.save(update_fields=["topic", "updated_at"])

    try:
        regenerate_caption.delay(item.id)
    except Exception:
        regenerate_caption(item.id)

    item.refresh_from_db()
    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Caption regeneration queued",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def item_approve_caption(request, item_id: int):
    """User approves the caption. Triggers Gemini image generation."""
    item = _get_item_for_user(request.user, item_id)
    if not (item.caption or "").strip():
        return _err("Cannot approve an empty caption", http=400)

    item.status = "image_generating"
    item.save(update_fields=["status", "updated_at"])

    try:
        generate_image_for_item.delay(item.id, "")
    except Exception:
        generate_image_for_item(item.id, "")

    item.refresh_from_db()
    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Caption approved, image generation started",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def item_regenerate_image(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    max_regens = getattr(settings, "CONTENT_PLAN_MAX_REGENS", 3)
    if item.image_regen_count >= max_regens:
        return _err(
            f"Image regeneration limit reached ({max_regens}).", http=429
        )

    prompt_override = (request.data.get("prompt_override") or "").strip()

    try:
        generate_image_for_item.delay(item.id, prompt_override)
    except Exception:
        generate_image_for_item(item.id, prompt_override)

    item.refresh_from_db()
    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Image regeneration queued",
    )


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def item_upload_image(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    upload = request.FILES.get("image")
    if not upload:
        return _err("image file is required", http=400)

    item.image = upload
    item.status = "image_pending_review"
    item.save(update_fields=["image", "status", "updated_at"])

    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Image uploaded",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def item_approve_image(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    if not item.image:
        return _err("Item has no image to approve", http=400)
    item.status = "approved"
    item.save(update_fields=["status", "updated_at"])
    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Item approved",
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def item_reject(request, item_id: int):
    item = _get_item_for_user(request.user, item_id)
    item.status = "rejected"
    item.save(update_fields=["status", "updated_at"])
    return _ok(
        ContentPlanItemSerializer(item, context={"request": request}).data,
        message="Item rejected",
    )
