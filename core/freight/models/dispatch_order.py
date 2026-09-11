# models/dispatch_order.py

from django.db import models

from freight.models import DispatchBatch, ShipmentOrder


class DispatchOrder(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        DELIVERED = "delivered", "Delivered"
        REJECTED = "rejected", "Rejected"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    batch = models.ForeignKey(
        DispatchBatch,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    order = models.ForeignKey(
        ShipmentOrder,
        on_delete=models.PROTECT,
        related_name="dispatch_items",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
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
        ordering = ["id"]

    def __str__(self):
        return (
            f"Dispatch Batch #{self.batch_id} - "
            f"{self.order.tracking_code}"
        )