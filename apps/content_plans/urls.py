from django.urls import path
from . import views

urlpatterns = [
    # AI key management
    path("ai-keys/gemini/", views.gemini_key, name="content_plans_gemini_key"),

    # Plans collection / detail
    path("content-plans/", views.plans_collection, name="content_plans_list"),
    path("content-plans/<int:plan_id>/", views.plan_detail, name="content_plans_detail"),
    path("content-plans/<int:plan_id>/progress/", views.plan_progress, name="content_plans_progress"),
    path("content-plans/<int:plan_id>/schedule/", views.plan_schedule, name="content_plans_schedule"),
    path("content-plans/<int:plan_id>/approve/", views.plan_approve, name="content_plans_approve"),

    # Item-level actions
    path("content-plans/items/<int:item_id>/", views.item_update, name="content_plan_item_update"),
    path("content-plans/items/<int:item_id>/regenerate-caption/", views.item_regenerate_caption, name="content_plan_item_regen_caption"),
    path("content-plans/items/<int:item_id>/approve-caption/", views.item_approve_caption, name="content_plan_item_approve_caption"),
    path("content-plans/items/<int:item_id>/regenerate-image/", views.item_regenerate_image, name="content_plan_item_regen_image"),
    path("content-plans/items/<int:item_id>/upload-image/", views.item_upload_image, name="content_plan_item_upload_image"),
    path("content-plans/items/<int:item_id>/approve-image/", views.item_approve_image, name="content_plan_item_approve_image"),
    path("content-plans/items/<int:item_id>/reject/", views.item_reject, name="content_plan_item_reject"),
]
