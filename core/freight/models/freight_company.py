from django.db import models


class FreightCompany(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)

    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Freight companies'
        ordering = ['name']

    def __str__(self):
        return self.name