from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def test_comments(request):
    return JsonResponse({
        "success": True,
        "message": "Comments app working"
    })


