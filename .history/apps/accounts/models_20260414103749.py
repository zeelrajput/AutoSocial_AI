from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    """
    Custom user model for autosocial AI software user
    This does not store any social media credentional
    """
    # basic info
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    ROLL_CHOICE = (
        ('admin','ADMIN'),
        ('user', 'USER')
    )
    role = models.CharField(max_length=10, choices=, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

