from django.urls import path
from .views import test_comments, generate_reply_api

urlpatterns = [
    # path("test/", test_comments, name="test_comments"),
    # path("test-check/", test_comments, name="test_check_comments"),
    path("generate-reply/", generate_reply_api, name="generate_reply"),
]