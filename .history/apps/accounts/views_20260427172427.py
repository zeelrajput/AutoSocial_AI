import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from apps.accounts.models import User, AgentDevice


@csrf_exempt
def register_user(request):
    if request.method == "POST":
        data = json.loads(request.body)

        user = User.objects.create_user(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password")
        )

        return JsonResponse({
            "success": True,
            "message": "User registration successfully done",
            "user_id": user.id
        })

    return JsonResponse({"success": False, "message": "Only POST allowed"}, status=405)


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)

        user = authenticate(
            request,
            email=data.get("email"),
            password=data.get("password")
        )

        if user:
            login(request, user)  # ✅ important
            return JsonResponse({
                "success": True,
                "message": "Login successfully done",
                "user_id": user.id
            })

        return JsonResponse({
            "success": False,
            "message": "Invalid credential"
        }, status=400)

    return JsonResponse({"success": False, "message": "Only POST allowed"}, status=405)


@login_required
def generate_agent_token(request):
    device_name = request.GET.get("device_name", "My Device")

    device = AgentDevice.objects.create(
        user=request.user,
        device_name=device_name
    )

    return JsonResponse({
        "success": True,
        "device_id": device.id,
        "agent_token": device.raw_token
    })