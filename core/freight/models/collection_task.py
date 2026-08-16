from django.conf import settings
from django.db import models


class CollectionTask(models.Model):

    class Type(models.TextChoices):
        CUSTOMER_DELIVERY = "customer_delivery", "Customer Delivery"
        COLLECTOR_PICKUP = "collector_pickup", "Collector Pickup"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(
        "freight.ShipmentOrder",
        on_delete=models.CASCADE,
        related_name="collection_task",
    )

    task_type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )

    collector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collection_tasks",
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
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
        permissions = [
            ("assign_collection_task", "Can assign collection task"),
            ("start_collection_task", "Can start collection task"),
            ("verify_collection_task", "Can verify collection task"),
            ("complete_collection_task", "Can complete collection task"),
            ("cancel_collection_task", "Can cancel collection task"),
        ]

    def __str__(self):
        return f"{self.order.tracking_code} - {self.get_task_type_display()}"