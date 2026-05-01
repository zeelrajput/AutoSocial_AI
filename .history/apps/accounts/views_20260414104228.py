from django.shortcuts import render
from accounts.models import *
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

@c
