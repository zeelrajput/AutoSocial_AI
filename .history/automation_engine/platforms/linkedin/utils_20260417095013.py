from django.utils import timezone

post.scheduled_time = timezone.make_aware(post.scheduled_time)