from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    """
    Custom user model for autosocial AI software user
    This does not store any social media credentional
    """

    
