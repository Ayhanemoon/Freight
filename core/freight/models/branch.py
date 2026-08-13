from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)

    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)

    phone = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'