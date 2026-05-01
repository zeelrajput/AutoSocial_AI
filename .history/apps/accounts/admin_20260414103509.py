from django.contrib import admin
from accounts.models import *
from django.contrib.auth.admin import u
# Register your models here.

admin.site.register(User)
