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
        ('linkedin', 'Linkedin'),
        ('x','X'),
    )

    # user who created post
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # content
    caption = models.TextField()
    media = models.FileField(upload_to='posts/', blank=True, null=True)

    # platform (single for now)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)

    # scheduling
    scheduled_time = models.DateTimeField()

    # status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.}"
