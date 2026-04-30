from django.shortcuts import render
from accounts.models import *
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import a
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

        user = 