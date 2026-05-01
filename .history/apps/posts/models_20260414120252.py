from django.db import models
from apps.accounts.models import User
# Create your models here.

class Post(models.Model):
    """
    stores post data for automatiom
    """

    STATUS_CHOICES = (
        ('pending','Pending'),
        ('scheduled', 'Scheduled'),
        ('posted','Posted'),
        ('failed','Failed'),
    )

    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'Linkedin')
    )
