from django.urls import path
from .views import test_comments

urlpatterns = [
    path("test/", test_comments, name="test_comments"),
    path("test-check/", test_comments, name="test_check_comments"),
]