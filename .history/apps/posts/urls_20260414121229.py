from django.urls import path
from apps.posts.models import Post
from 

urlpatterns = [
    path('create/', views.create_post)
]