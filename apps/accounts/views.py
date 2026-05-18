import json

from django.http import JsonResponse
from django.contrib.auth import authenticate

from apps.accounts.models import User, AgentDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    data = request.data

    try:
        user = User.objects.create_user(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password")
        )
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

    return JsonResponse({
        "success": True,
        "message": "User registration successfully done",
        "data": {
            "user_id": user.id
        }
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    data = request.data

    user = authenticate(
        request,
        email=data.get("email"),
        password=data.get("password")
    )

    if user:
        refresh = RefreshToken.for_user(user)

        device = AgentDevice.objects.create(
            user=user,
            device_name=data.get("device_name", "My Device")
        )

        return JsonResponse({
            "success": True,
            "message": "Login successfully done",
            "data": {
                "user_id": user.id,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "device_id": device.id,
                "agent_token": device.raw_token
            }
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid credential"
    }, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
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