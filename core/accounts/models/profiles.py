from django.db import models
from .users import User
from django.dispatch import receiver
from django.db.models.signals import post_save


class Profile(models.Model):
    """User profile model to store additional information about the user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile for each new user."""
    if created:
        Profile.objects.create(user=instance)
