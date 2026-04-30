from django.urls import path
from . import views

urlpatterns = [
    path("run/", views.run_schedular, name="run_schedular"),
    path("send-task/<int:post_id>/", views.send_task_to_agent, name="send_task_to_agent"),
]