from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def test_comments(request):
    return JsonResponse({
        "success": True,
        "message": "Comments app working"
    })
