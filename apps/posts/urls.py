from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_post),
    path('list/', views.list_posts),
    path('generate-ai-caption/', views.generate_ai_caption),
    path("check-comments/", views.trigger_comment_check),
    # path("generate-reply/", views.generate_reply_api),
]

