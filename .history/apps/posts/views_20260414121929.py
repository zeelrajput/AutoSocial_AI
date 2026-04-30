from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.posts.models import Post
from apps.accounts.models import User

# Create your views here.

@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        data = JsonResponse()