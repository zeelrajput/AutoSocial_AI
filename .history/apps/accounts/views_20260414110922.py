from django.shortcuts import render
from apps.accounts.models import User
from django.http import JsonResponse

import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
# Create your views here.

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        user = User.objects.create(
            username = data.get('username'),
            email = data.get('email'),
            password = data.get('password')
        )

        return JsonResponse({"message":"user registration successfully done"})
    

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        user = authenticate(
            username = data.get('username'),
            password = data.get('password')
        )

        if user:
            return JsonResponse({"message":"login successfully done"})
        else:
            return JsonResponse({"message":"invalid credintional"}, status=400)
        