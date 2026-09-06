from django.conf import settings
from django.db import models

from freight.models import ShipmentOrder


class Invoice(models.Model):

    order = models.OneToOneField(
        ShipmentOrder,
        on_delete=models.PROTECT,
        related_name="invoice",
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
    )

    issued_at = models.DateTimeField()

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_invoices",
    )

    # Customer snapshot
    customer_name = models.CharField(
        max_length=255,
    )

    customer_mobile = models.CharField(
        max_length=20,
    )

    customer_address = models.TextField(
        blank=True,
    )

    # Receiver snapshot
    receiver_name = models.CharField(
        max_length=255,
    )

    receiver_mobile = models.CharField(
        max_length=20,
    )

    receiver_address = models.TextField()

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return self.invoice_number