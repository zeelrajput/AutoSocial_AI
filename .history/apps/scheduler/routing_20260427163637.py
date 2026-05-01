from django.urls import re_path
from .consumers import AgentConsumer

websocket_urlpatterns = [
    # OLD (keep it)
    re_path(r"ws/agent/(?P<user_id>\d+)/$", AgentConsumer.as_asgi()),

    # NEW (for token-based multi-user)
    re_path(r"ws/agent/$", AgentConsumer.as_asgi()),
]