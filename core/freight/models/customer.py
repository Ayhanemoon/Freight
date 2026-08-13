from django.conf import settings
from django.db import models


class Customer(models.Model):
    class CustomerType(models.TextChoices):
        PERSON = 'person', 'Person'
        COMPANY = 'company', 'Company'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.PERSON,
    )

    # Person fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    national_id = models.CharField(max_length=20, blank=True)

    # Company fields
    company_name = models.CharField(max_length=255, blank=True)
    company_registration_no = models.CharField(max_length=50, blank=True)
    economic_code = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def display_name(self):
        if self.customer_type == self.CustomerType.COMPANY:
            return self.company_name or str(self.user.mobile)

        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or str(self.user.mobile)

    def __str__(self):
        return self.display_name