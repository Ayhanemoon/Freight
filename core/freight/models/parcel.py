from django.conf import settings
from django.db import models

from freight.models.shipment_order import ShipmentOrder


class Parcel(models.Model):

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        DIFFERENCE_FOUND = "difference_found", "Difference Found"

    order = models.ForeignKey(
        ShipmentOrder,
        on_delete=models.CASCADE,
        related_name="parcels",
    )

    parcel_number = models.PositiveIntegerField()

    # Customer declaration
    declared_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    declared_length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    declared_width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    declared_height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    contents_description = models.TextField(
        blank=True,
    )

    # Physical verification
    verified_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    verified_length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    verified_width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    verified_height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_parcels",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["parcel_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "parcel_number"],
                name="unique_parcel_number_per_order",
            )
        ]

    def __str__(self):
        return f"{self.order.tracking_code} - Parcel {self.parcel_number}"