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
    role = models.CharField(max_length=10, choices=ROLL_CHOICE, default='user')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

import secrets
import hashlib

class AgentDevice(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agent_devices"
    )

    device_name = models.CharField(max_length=255)

    token_hash = models.CharField(max_length=128, unique=True, blank=True)
    raw_token = models.CharField(max_length=128, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)

    last_seen = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token_hash:
            raw_token = secrets.token_urlsafe(48)
            self.raw_token = raw_token
            self.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"