from django.urls import path
from apps.posts.models import Post
from . import views

urlpatterns = [
    path('create/', views.create_post),
    path('list/', vi)
]