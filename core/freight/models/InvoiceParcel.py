from django.db import models

from freight.models.invoice import Invoice
from freight.models.parcel import Parcel


class InvoiceParcel(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="parcels",
    )

    parcel = models.ForeignKey(
        Parcel,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )

    # Snapshot fields
    parcel_number = models.PositiveIntegerField()

    parcel_name = models.CharField(
        max_length=255,
        blank=True,
    )

    parcel_type = models.CharField(
        max_length=100,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["parcel_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "parcel"],
                name="unique_invoice_parcel",
            )
        ]

    def __str__(self):
        return (
            f"{self.invoice.invoice_number} - "
            f"Parcel {self.parcel_number}"
        )