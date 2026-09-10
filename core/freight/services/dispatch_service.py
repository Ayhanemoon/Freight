from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from freight.models import DispatchBatch, DispatchOrder, ShipmentOrder, DispatchFreightAssignment, ShipmentStatusHistory


def _check_branch_access(*, user, branch_id):
    if user.is_superuser:
        return

    if user.branch_id != branch_id:
        raise PermissionDenied(
            "You cannot manage dispatch operations outside your branch."
        )


def _check_dispatch_permission(*, user, permission):
    if user.is_superuser:
        return

    if not user.has_perm(permission):
        raise PermissionDenied(
            "You do not have permission to perform this dispatch action."
        )


@transaction.atomic
def create_dispatch_batch(*, branch, created_by, scheduled_at=None, notes=""):
    """
    Create a new dispatch batch for a branch.

    A batch initially contains no orders and no freight assignments.
    Orders are added separately.
    """

    _check_dispatch_permission(
        user=created_by,
        permission="freight.add_dispatchbatch",
    )

    _check_branch_access(
        user=created_by,
        branch_id=branch.id,
    )

    batch = DispatchBatch.objects.create(
        branch=branch,
        scheduled_at=scheduled_at,
        notes=notes,
        created_by=created_by,
    )

    return batch


@transaction.atomic
def add_order_to_batch(*, batch, order, added_by):
    """
    Add a ShipmentOrder to a dispatch batch.

    Rules:
    - Batch must belong to the same branch as the order.
    - Order must be READY_FOR_DISPATCH.
    - Order cannot already exist in this batch.
    - Order cannot belong to another active dispatch batch.
    """

    _check_dispatch_permission(
        user=added_by,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=added_by,
        branch_id=batch.branch_id,
    )

    if order.branch_id != batch.branch_id:
        raise ValidationError(
            "Order and dispatch batch must belong to the same branch."
        )

    if batch.status not in {
        DispatchBatch.Status.DRAFT,
        DispatchBatch.Status.READY,
    }:
        raise ValidationError(
            "Orders can only be added to a draft or ready dispatch batch."
        )

    if order.status != ShipmentOrder.Status.READY_FOR_DISPATCH:
        raise ValidationError(
            "Only orders ready for dispatch can be added to a dispatch batch."
        )

    if DispatchOrder.objects.filter(
        batch=batch,
        order=order,
    ).exists():
        raise ValidationError(
            "This order is already part of this dispatch batch."
        )

    active_batch_exists = DispatchOrder.objects.filter(
        order=order,
        batch__status__in=[
            DispatchBatch.Status.DRAFT,
            DispatchBatch.Status.READY,
            DispatchBatch.Status.ASSIGNED,
            DispatchBatch.Status.IN_PROGRESS,
        ],
    ).exclude(
        batch=batch,
    ).exists()

    if active_batch_exists:
        raise ValidationError(
            "This order already belongs to another active dispatch batch."
        )

    dispatch_order = DispatchOrder.objects.create(
        batch=batch,
        order=order,
        status=DispatchOrder.Status.PENDING,
    )

    return dispatch_order


@transaction.atomic
def remove_order_from_batch(*, dispatch_order, removed_by):
    """
    Remove an order from a batch before dispatch starts.
    """

    batch = dispatch_order.batch

    _check_dispatch_permission(
        user=removed_by,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=removed_by,
        branch_id=batch.branch_id,
    )

    if batch.status not in {
        DispatchBatch.Status.DRAFT,
        DispatchBatch.Status.READY,
    }:
        raise ValidationError(
            "Orders cannot be removed after dispatch has started."
        )

    if dispatch_order.status != DispatchOrder.Status.PENDING:
        raise ValidationError(
            "Only pending dispatch orders can be removed."
        )

    dispatch_order.delete()

@transaction.atomic
def assign_dispatcher(*, batch, dispatcher, assigned_by):
    """
    Assign a dispatcher to a dispatch batch.
    """

    _check_dispatch_permission(
        user=assigned_by,
        permission="freight.assign_dispatcher",
    )

    _check_branch_access(
        user=assigned_by,
        branch_id=batch.branch_id,
    )

    if batch.status not in {
        DispatchBatch.Status.DRAFT,
        DispatchBatch.Status.READY,
    }:
        raise ValidationError(
            "Dispatcher can only be assigned to a draft or ready batch."
        )

    if not dispatcher.is_active:
        raise ValidationError(
            "Selected dispatcher is not active."
        )

    if not dispatcher.groups.filter(
        name="Dispatcher"
    ).exists():
        raise ValidationError(
            "Selected user is not a Dispatcher."
        )

    if dispatcher.branch_id != batch.branch_id:
        raise ValidationError(
            "Dispatcher must belong to the same branch as the batch."
        )

    batch.dispatcher = dispatcher
    batch.status = DispatchBatch.Status.ASSIGNED

    batch.save(
        update_fields=[
            "dispatcher",
            "status",
            "updated_at",
        ]
    )

    return batch

@transaction.atomic
def mark_batch_ready(*, batch, user):
    """
    Mark a dispatch batch as ready for dispatcher assignment/start.
    """

    _check_dispatch_permission(
        user=user,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=user,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.DRAFT:
        raise ValidationError(
            "Only draft batches can be marked as ready."
        )

    if not batch.orders.exists():
        raise ValidationError(
            "Cannot mark an empty dispatch batch as ready."
        )

    batch.status = DispatchBatch.Status.READY

    batch.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return batch

@transaction.atomic
def start_dispatch(*, batch, user):
    """
    Start a dispatch batch.

    The batch must have:
    - an assigned dispatcher
    - at least one order
    """

    _check_dispatch_permission(
        user=user,
        permission="freight.start_dispatch",
    )

    _check_branch_access(
        user=user,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.ASSIGNED:
        raise ValidationError(
            "Only assigned dispatch batches can be started."
        )

    if batch.dispatcher_id != user.id and not user.is_superuser:
        raise PermissionDenied(
            "Only the assigned dispatcher can start this batch."
        )

    if not batch.orders.exists():
        raise ValidationError(
            "Cannot start an empty dispatch batch."
        )

    now = timezone.now()

    batch.status = DispatchBatch.Status.IN_PROGRESS
    batch.dispatched_at = now

    batch.save(
        update_fields=[
            "status",
            "dispatched_at",
            "updated_at",
        ]
    )

    return batch

@transaction.atomic
def assign_freight_company(
    *,
    dispatch_order,
    freight_company,
    assigned_by,
    payer,
    freight_amount=None,
    notes="",
):
    """
    Create a new freight-company assignment attempt for a dispatch order.

    A dispatch order may have multiple assignments over time:
        Freight A -> REJECTED
        Freight B -> REJECTED
        Freight C -> ACCEPTED

    Only one assignment can be active at a time.
    """

    batch = dispatch_order.batch
    order = dispatch_order.order

    _check_dispatch_permission(
        user=assigned_by,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=assigned_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "Freight company can only be assigned while the batch is in progress."
        )

    if dispatch_order.status not in {
        DispatchOrder.Status.PENDING,
        DispatchOrder.Status.IN_PROGRESS,
    }:
        raise ValidationError(
            "Freight company cannot be assigned to this dispatch order "
            "in its current status."
        )

    if order.status != ShipmentOrder.Status.READY_FOR_DISPATCH:
        raise ValidationError(
            "Shipment order is not ready for dispatch."
        )

    active_assignment_exists = DispatchFreightAssignment.objects.filter(
        dispatch_order=dispatch_order,
        status__in=[
            DispatchFreightAssignment.Status.SELECTED,
            DispatchFreightAssignment.Status.ACCEPTED,
        ],
    ).exists()

    if active_assignment_exists:
        raise ValidationError(
            "This dispatch order already has an active freight-company assignment."
        )

    if freight_amount is not None and freight_amount < 0:
        raise ValidationError(
            "Freight amount cannot be negative."
        )

    assignment = DispatchFreightAssignment.objects.create(
        dispatch_order=dispatch_order,
        freight_company=freight_company,
        status=DispatchFreightAssignment.Status.SELECTED,
        payer=payer,
        freight_amount=freight_amount,
        notes=notes,
        created_by=assigned_by,
    )

    if dispatch_order.status == DispatchOrder.Status.PENDING:
        dispatch_order.status = DispatchOrder.Status.IN_PROGRESS
        dispatch_order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return assignment

@transaction.atomic
def accept_freight_assignment(
    *,
    assignment,
    accepted_by,
    freight_amount=None,
    freight_invoice_number="",
    freight_invoice_file=None,
    notes="",
):
    """
    Mark a selected freight-company assignment as accepted.
    """

    _check_dispatch_permission(
        user=accepted_by,
        permission="freight.change_dispatchbatch",
    )

    batch = assignment.dispatch_order.batch

    _check_branch_access(
        user=accepted_by,
        branch_id=batch.branch_id,
    )

    if assignment.status != (
        assignment.Status.SELECTED
    ):
        raise ValidationError(
            "Only selected freight assignments can be accepted."
        )

    if freight_amount is not None:
        if freight_amount < 0:
            raise ValidationError(
                "Freight amount cannot be negative."
            )

        assignment.freight_amount = freight_amount

    assignment.status = assignment.Status.ACCEPTED
    assignment.accepted_at = timezone.now()

    if freight_invoice_number:
        assignment.freight_invoice_number = freight_invoice_number

    if freight_invoice_file is not None:
        assignment.freight_invoice_file = freight_invoice_file

    if notes:
        assignment.notes = notes

    assignment.save(
        update_fields=[
            "status",
            "accepted_at",
            "freight_amount",
            "freight_invoice_number",
            "freight_invoice_file",
            "notes",
            "updated_at",
        ]
    )

    return assignment

@transaction.atomic
def reject_freight_assignment(
    *,
    assignment,
    rejected_by,
    rejection_reason,
):
    """
    Reject the current freight-company assignment.

    The dispatch order remains active and can be assigned
    to another freight company.
    """

    _check_dispatch_permission(
        user=rejected_by,
        permission="freight.change_dispatchbatch",
    )

    batch = assignment.dispatch_order.batch

    _check_branch_access(
        user=rejected_by,
        branch_id=batch.branch_id,
    )

    if assignment.status != assignment.Status.SELECTED:
        raise ValidationError(
            "Only selected freight assignments can be rejected."
        )

    if not rejection_reason.strip():
        raise ValidationError(
            "Rejection reason is required."
        )

    assignment.status = assignment.Status.REJECTED
    assignment.rejection_reason = rejection_reason
    assignment.save(
        update_fields=[
            "status",
            "rejection_reason",
            "updated_at",
        ]
    )

    return assignment

@transaction.atomic
def mark_freight_assignment_delivered(
    *,
    assignment,
    delivered_by,
    notes="",
):
    """
    Mark the current freight-company assignment as delivered.

    This means the shipment was successfully handed over
    to the selected main freight company.
    """

    _check_dispatch_permission(
        user=delivered_by,
        permission="freight.change_dispatchbatch",
    )

    dispatch_order = assignment.dispatch_order
    batch = dispatch_order.batch

    _check_branch_access(
        user=delivered_by,
        branch_id=batch.branch_id,
    )

    if assignment.status != assignment.Status.ACCEPTED:
        raise ValidationError(
            "Only accepted freight assignments can be marked as delivered."
        )

    if dispatch_order.status not in {
        DispatchOrder.Status.IN_PROGRESS,
        DispatchOrder.Status.PENDING_APPROVAL,
    }:
        raise ValidationError(
            "This dispatch order cannot be marked as delivered "
            "in its current status."
        )

    now = timezone.now()

    assignment.status = assignment.Status.DELIVERED
    assignment.delivered_at = now

    if notes:
        assignment.notes = notes

    assignment.save(
        update_fields=[
            "status",
            "delivered_at",
            "notes",
            "updated_at",
        ]
    )

    dispatch_order.status = DispatchOrder.Status.PENDING_APPROVAL

    dispatch_order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return assignment

@transaction.atomic
def return_dispatch_order(
    *,
    dispatch_order,
    returned_by,
    notes="",
):
    """
    Return a dispatch order to the branch because it could not
    be delivered to a main freight company during this batch.

    The ShipmentOrder remains READY_FOR_DISPATCH so it can be
    added to a future dispatch batch.
    """

    _check_dispatch_permission(
        user=returned_by,
        permission="freight.change_dispatchbatch",
    )

    batch = dispatch_order.batch
    order = dispatch_order.order

    _check_branch_access(
        user=returned_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "An order can only be returned while the batch is in progress."
        )

    if dispatch_order.status != DispatchOrder.Status.IN_PROGRESS:
        raise ValidationError(
            "Only in-progress dispatch orders can be returned."
        )

    dispatch_order.status = DispatchOrder.Status.RETURNED

    if notes:
        dispatch_order.notes = notes

    dispatch_order.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    # The ShipmentOrder is deliberately NOT cancelled.
    # It remains ready for another dispatch attempt.
    if order.status != ShipmentOrder.Status.READY_FOR_DISPATCH:
        previous_status = order.status

        order.status = ShipmentOrder.Status.READY_FOR_DISPATCH
        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        ShipmentStatusHistory.objects.create(
            order=order,
            from_status=previous_status,
            to_status=ShipmentOrder.Status.READY_FOR_DISPATCH,
            changed_by=returned_by,
            note=notes or "Shipment returned from dispatch.",
        )

    return dispatch_order

@transaction.atomic
def approve_dispatch_handover(
    *,
    dispatch_order,
    approved_by,
    notes="",
):
    """
    Approve a successfully completed handover to the main freight company.
    """

    _check_dispatch_permission(
        user=approved_by,
        permission="freight.change_dispatchbatch",
    )

    batch = dispatch_order.batch
    order = dispatch_order.order

    _check_branch_access(
        user=approved_by,
        branch_id=batch.branch_id,
    )

    if dispatch_order.status != DispatchOrder.Status.PENDING_APPROVAL:
        raise ValidationError(
            "This dispatch order is not pending approval."
        )

    assignment = dispatch_order.freight_assignments.filter(
        status=DispatchFreightAssignment.Status.DELIVERED
    ).order_by("-delivered_at").first()

    if not assignment:
        raise ValidationError(
            "No delivered freight assignment exists for this dispatch order."
        )

    dispatch_order.status = DispatchOrder.Status.APPROVED

    if notes:
        dispatch_order.notes = notes

    dispatch_order.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    order.status = ShipmentOrder.Status.DISPATCHED_TO_FREIGHT
    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return dispatch_order

@transaction.atomic
def complete_dispatch_batch(*, batch, completed_by, notes=""):
    """
        Finish the physical dispatch operation.

        Every dispatch order must have a final physical outcome:
            - DELIVERED
            - RETURNED
            - CANCELLED

        The batch then moves to DELIVERED.
    """

    _check_dispatch_permission(
        user=completed_by,
        permission="freight.complete_dispatch",
    )

    _check_branch_access(
        user=completed_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "Only in-progress dispatch batches can be completed."
        )

    dispatch_orders = batch.orders.all()

    if not dispatch_orders.exists():
        raise ValidationError(
            "Cannot complete an empty dispatch batch."
        )

    unfinished_exists = dispatch_orders.exclude(
        status__in=[
            DispatchOrder.Status.DELIVERED,
            DispatchOrder.Status.RETURNED,
            DispatchOrder.Status.CANCELLED,
        ]
    ).exists()

    if unfinished_exists:
        raise ValidationError(
            "All orders must be delivered, returned, or cancelled "
            "before the dispatch batch can be completed."
        )

    now = timezone.now()

    batch.status = DispatchBatch.Status.DELIVERED
    batch.delivered_at = now
    batch.completed_at = now

    if notes:
        batch.notes = notes

    batch.save(
        update_fields=[
            "status",
            "delivered_at",
            "completed_at",
            "notes",
            "updated_at",
        ]
    )

    return batch