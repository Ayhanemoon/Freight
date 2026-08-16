import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from freight.models.branch import Branch
from freight.models.customer import Customer
from freight.models.freight_company import FreightCompany


class ShipmentOrder(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted'
        OPERATOR_REVIEW = 'operator_review', 'Operator Review'
        APPROVED_FOR_COLLECTION = 'approved_for_collection', 'Approved for Collection'
        COLLECTED = 'collected', 'Collected'
        RECEIVED_AT_BRANCH = 'received_at_branch', 'Received at Branch'
        INVOICE_REGISTERED = 'invoice_registered', 'Invoice Registered'
        READY_FOR_DISPATCH = 'ready_for_dispatch', 'Ready for Dispatch'
        DISPATCHED_TO_FREIGHT = 'dispatched_to_freight', 'Dispatched to Freight'
        HANDOVER_PENDING_APPROVAL = 'handover_pending_approval', 'Handover Pending Approval'
        HANDOVER_APPROVED = 'handover_approved', 'Handover Approved'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    tracking_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    barcode = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='orders',
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
    )

    preferred_freight_company = models.ForeignKey(
        FreightCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_orders',
    )

    # Sender snapshot
    sender_name = models.CharField(max_length=255)
    sender_mobile = models.CharField(max_length=20)
    sender_address = models.TextField()

    # Receiver snapshot
    receiver_name = models.CharField(max_length=255)
    receiver_mobile = models.CharField(max_length=20)
    receiver_address = models.TextField()

    

    shipment_description = models.TextField(blank=True)

    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    submitted_at = models.DateTimeField(default=timezone.now)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_orders',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            today = timezone.localdate()
            date_part = today.strftime('%Y%m%d')

            last_order = ShipmentOrder.objects.filter(
                created_at__date=today
            ).order_by('-id').first()

            next_number = 1 if not last_order else last_order.id + 1

            self.tracking_code = f'FR-{date_part}-{next_number:06d}'
            self.barcode = self.tracking_code

        super().save(*args, **kwargs)

    def __str__(self):
        return self.tracking_code