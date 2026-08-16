from django.conf import settings
from django.db import models


class ShipmentStatusHistory(models.Model):

    shipment = models.ForeignKey(
        "freight.ShipmentOrder",
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    from_status = models.CharField(
        max_length=40,
        null=True,
        blank=True,
    )

    to_status = models.CharField(
        max_length=40,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shipment_status_changes",
    )

    note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.shipment.tracking_code}: "
            f"{self.from_status or '-'} → {self.to_status}"
        )