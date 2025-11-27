from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def avatar_upload_to(instance, filename):
    return f"avatars/{timezone.now().strftime('%Y/%m')}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, default='')
    contact = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)
    telegram = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
