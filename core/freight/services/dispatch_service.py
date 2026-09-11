from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from freight.models import (
    DispatchBatch,
    DispatchFreightAssignment,
    DispatchOrder,
    ShipmentOrder,
    ShipmentStatusHistory,
    Invoice,
    InvoiceCharge,
)


BATCH_TRANSITIONS = {
    DispatchBatch.Status.DRAFT: {
        DispatchBatch.Status.READY,
        DispatchBatch.Status.CANCELLED,
    },
    DispatchBatch.Status.READY: {
        DispatchBatch.Status.ASSIGNED,
        DispatchBatch.Status.CANCELLED,
    },
    DispatchBatch.Status.ASSIGNED: {
        DispatchBatch.Status.IN_PROGRESS,
        DispatchBatch.Status.CANCELLED,
    },
    DispatchBatch.Status.IN_PROGRESS: {
        DispatchBatch.Status.COMPLETED,
        DispatchBatch.Status.CANCELLED,
    },
    DispatchBatch.Status.COMPLETED: set(),
    DispatchBatch.Status.CANCELLED: set(),
}


DISPATCH_ORDER_TRANSITIONS = {
    DispatchOrder.Status.PENDING: {
        DispatchOrder.Status.IN_PROGRESS,
        DispatchOrder.Status.CANCELLED,
    },
    DispatchOrder.Status.IN_PROGRESS: {
        DispatchOrder.Status.DELIVERED,
        DispatchOrder.Status.REJECTED,
        DispatchOrder.Status.CANCELLED,
    },
    DispatchOrder.Status.DELIVERED: set(),
    DispatchOrder.Status.REJECTED: {
        DispatchOrder.Status.RETURNED,
        DispatchOrder.Status.CANCELLED,
    },
    DispatchOrder.Status.RETURNED: set(),
    DispatchOrder.Status.CANCELLED: set(),
}


ASSIGNMENT_TRANSITIONS = {
    DispatchFreightAssignment.Status.DISPATCHING: {
        DispatchFreightAssignment.Status.PENDING_APPROVAL,
        DispatchFreightAssignment.Status.REJECTED,
        DispatchFreightAssignment.Status.CANCELLED,
    },
    DispatchFreightAssignment.Status.PENDING_APPROVAL: {
        DispatchFreightAssignment.Status.APPROVED,
        DispatchFreightAssignment.Status.CANCELLED,
    },
    DispatchFreightAssignment.Status.APPROVED: set(),
    DispatchFreightAssignment.Status.REJECTED: set(),
    DispatchFreightAssignment.Status.CANCELLED: set(),
}


def _check_dispatch_permission(*, user, permission):
    if user.is_superuser:
        return

    if not user.has_perm(permission):
        raise PermissionDenied(
            "You do not have permission to perform "
            "this dispatch action."
        )

def _check_branch_access(*, user, branch_id):
    if user.is_superuser:
        return

    if user.branch_id != branch_id:
        raise PermissionDenied(
            "You cannot manage dispatch operations "
            "outside your branch."
        )

def _validate_transition(
    *,
    current_status,
    new_status,
    transitions,
):
    if current_status == new_status:
        raise ValidationError(
            f"Object is already {current_status}."
        )

    allowed_statuses = transitions.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValidationError(
            f"Cannot change status from "
            f"{current_status} to {new_status}."
        )

@transaction.atomic
def create_dispatch_batch(
    *,
    branch,
    created_by,
    scheduled_at=None,
    notes="",
):
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
        created_by=created_by,
        scheduled_at=scheduled_at,
        notes=notes,
        status=DispatchBatch.Status.DRAFT,
    )

    return batch

@transaction.atomic
def add_order_to_batch(
    *,
    batch,
    order,
    added_by,
):
    _check_dispatch_permission(
        user=added_by,
        permission="freight.add_order_to_dispatch",
    )

    _check_branch_access(
        user=added_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.DRAFT:
        raise ValidationError(
            "Orders can only be added to a draft dispatch batch."
        )

    if order.status != ShipmentOrder.Status.READY_FOR_DISPATCH:
        raise ValidationError(
            "Only shipments ready for dispatch can be added."
        )

    if batch.orders.filter(order=order).exists():
        raise ValidationError(
            "This shipment is already in the dispatch batch."
        )

    return DispatchOrder.objects.create(
        batch=batch,
        order=order,
        status=DispatchOrder.Status.PENDING,
    )

@transaction.atomic
def remove_order_from_batch(
    *,
    dispatch_order,
    removed_by,
):
    _check_dispatch_permission(
        user=removed_by,
        permission="freight.remove_order_from_dispatch",
    )

    batch = dispatch_order.batch

    _check_branch_access(
        user=removed_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.DRAFT:
        raise ValidationError(
            "Orders can only be removed from a draft dispatch batch."
        )

    dispatch_order.delete()

@transaction.atomic
def make_batch_ready(
    *,
    batch,
    changed_by,
):
    _check_dispatch_permission(
        user=changed_by,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=changed_by,
        branch_id=batch.branch_id,
    )

    _validate_transition(
        current_status=batch.status,
        new_status=DispatchBatch.Status.READY,
        transitions=BATCH_TRANSITIONS,
    )

    dispatch_orders = batch.orders.all()

    if not dispatch_orders.exists():
        raise ValidationError(
            "A dispatch batch must contain at least one order."
        )

    for dispatch_order in dispatch_orders:
        if not dispatch_order.freight_assignments.filter(
            status=DispatchFreightAssignment.Status.DISPATCHING
        ).exists():
            raise ValidationError(
                f"Dispatch order "
                f"{dispatch_order.order.tracking_code} "
                f"has no freight-company assignment."
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
def assign_dispatcher(
    *,
    batch,
    dispatcher,
    assigned_by,
):
    _check_dispatch_permission(
        user=assigned_by,
        permission="freight.assign_dispatcher",
    )

    _check_branch_access(
        user=assigned_by,
        branch_id=batch.branch_id,
    )

    _validate_transition(
        current_status=batch.status,
        new_status=DispatchBatch.Status.ASSIGNED,
        transitions=BATCH_TRANSITIONS,
    )

    if not dispatcher.is_active:
        raise ValidationError(
            "Selected dispatcher is not active."
        )

    if dispatcher.branch_id != batch.branch_id:
        raise ValidationError(
            "Dispatcher must belong to the same branch "
            "as the dispatch batch."
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
def assign_freight_company(
    *,
    dispatch_order,
    freight_company,
    payer,
    created_by,
    freight_amount=None,
):
    _check_dispatch_permission(
        user=created_by,
        permission="freight.add_order_to_dispatch",
    )

    batch = dispatch_order.batch

    _check_branch_access(
        user=created_by,
        branch_id=batch.branch_id,
    )

    if batch.status not in {
        DispatchBatch.Status.DRAFT,
        DispatchBatch.Status.IN_PROGRESS,
    }:
        raise ValidationError(
            "A freight company can only be assigned while "
            "the batch is in draft or in progress."
        )

    if dispatch_order.status not in {
        DispatchOrder.Status.PENDING,
        DispatchOrder.Status.IN_PROGRESS,
    }:
        raise ValidationError(
            "A freight company can only be assigned to a "
            "pending or in-progress dispatch order."
        )

    if payer not in {
        DispatchFreightAssignment.Payer.SENDER,
        DispatchFreightAssignment.Payer.RECEIVER,
    }:
        raise ValidationError(
            "Invalid payer."
        )

    active_assignment = dispatch_order.freight_assignments.filter(
        status=DispatchFreightAssignment.Status.DISPATCHING
    ).exists()

    if active_assignment:
        raise ValidationError(
            "This dispatch order already has an active "
            "freight-company assignment."
        )

    return DispatchFreightAssignment.objects.create(
        dispatch_order=dispatch_order,
        freight_company=freight_company,
        payer=payer,
        freight_amount=freight_amount,
        created_by=created_by,
        status=DispatchFreightAssignment.Status.DISPATCHING,
    )

@transaction.atomic
def get_order_freight_amount(
    *,
    dispatch_order,
):
    order = dispatch_order.order

    try:
        invoice = order.invoice
    except Invoice.DoesNotExist:
        raise ValidationError(
            "This shipment does not have an invoice."
        )

    if invoice.total_cost <= 0:
        raise ValidationError(
            "The shipment invoice does not have a valid total cost."
        )

    return invoice.total_cost

@transaction.atomic
def start_dispatch(
    *,
    batch,
    started_by,
):
    _check_dispatch_permission(
        user=started_by,
        permission="freight.start_dispatch",
    )

    _check_branch_access(
        user=started_by,
        branch_id=batch.branch_id,
    )

    _validate_transition(
        current_status=batch.status,
        new_status=DispatchBatch.Status.IN_PROGRESS,
        transitions=BATCH_TRANSITIONS,
    )

    if batch.dispatcher_id != started_by.id:
        raise PermissionDenied(
            "Only the assigned dispatcher can start this dispatch."
        )

    dispatch_orders = batch.orders.select_for_update().all()

    if not dispatch_orders.exists():
        raise ValidationError(
            "A dispatch batch must contain at least one order."
        )

    now = timezone.now()

    for dispatch_order in dispatch_orders:
        _validate_transition(
            current_status=dispatch_order.status,
            new_status=DispatchOrder.Status.IN_PROGRESS,
            transitions=DISPATCH_ORDER_TRANSITIONS,
        )

        assignment = (
            dispatch_order.freight_assignments
            .select_for_update()
            .filter(
                status=DispatchFreightAssignment.Status.DISPATCHING
            )
            .order_by("-assigned_at")
            .first()
        )

        if not assignment:
            raise ValidationError(
                f"Dispatch order "
                f"{dispatch_order.order.tracking_code} "
                f"has no active freight-company assignment."
            )

        dispatch_order.status = DispatchOrder.Status.IN_PROGRESS

        dispatch_order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

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
def mark_freight_assignment_delivered(
    *,
    assignment,
    delivered_by,
    freight_invoice_number,
    freight_invoice_file=None,
    notes="",
):
    _check_dispatch_permission(
        user=delivered_by,
        permission="freight.start_dispatch",
    )

    dispatch_order = assignment.dispatch_order
    batch = dispatch_order.batch

    _check_branch_access(
        user=delivered_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "The dispatch batch must be in progress."
        )

    if dispatch_order.status != DispatchOrder.Status.IN_PROGRESS:
        raise ValidationError(
            "Only in-progress dispatch orders can be marked as delivered."
        )

    if assignment.status != DispatchFreightAssignment.Status.DISPATCHING:
        raise ValidationError(
            "Only dispatching freight assignments can be marked "
            "as pending approval."
        )

    if not freight_invoice_number:
        raise ValidationError(
            "Freight invoice number is required."
        )

    now = timezone.now()

    assignment.status = (
        DispatchFreightAssignment.Status.PENDING_APPROVAL
    )
    assignment.freight_invoice_number = freight_invoice_number

    if freight_invoice_file is not None:
        assignment.freight_invoice_file = freight_invoice_file

    if notes:
        assignment.notes = notes

    assignment.save(
        update_fields=[
            "status",
            "freight_invoice_number",
            "freight_invoice_file",
            "notes",
            "updated_at",
        ]
    )

    dispatch_order.status = DispatchOrder.Status.DELIVERED

    dispatch_order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return assignment

@transaction.atomic
def approve_dispatch_handover(
    *,
    dispatch_order,
    approved_by,
    notes="",
):
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

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "The dispatch batch must be in progress."
        )

    if dispatch_order.status != DispatchOrder.Status.DELIVERED:
        raise ValidationError(
            "Only delivered dispatch orders can be approved."
        )

    assignment = (
        dispatch_order.freight_assignments
        .filter(
            status=DispatchFreightAssignment.Status.PENDING_APPROVAL
        )
        .order_by("-updated_at")
        .first()
    )

    if not assignment:
        raise ValidationError(
            "No freight assignment is pending approval."
        )

    now = timezone.now()

    assignment.status = DispatchFreightAssignment.Status.APPROVED
    assignment.approved_at = now

    if notes:
        assignment.notes = notes

    assignment.save(
        update_fields=[
            "status",
            "approved_at",
            "notes",
            "updated_at",
        ]
    )

    old_status = order.status
    new_status = ShipmentOrder.Status.DISPATCHED_TO_FREIGHT

    if old_status != new_status:
        order.status = new_status

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        ShipmentStatusHistory.objects.create(
            shipment=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=approved_by,
            note=notes,
        )

    return dispatch_order


@transaction.atomic
def reject_dispatch_order(
    *,
    dispatch_order,
    rejected_by,
    reason,
    notes="",
):
    _check_dispatch_permission(
        user=rejected_by,
        permission="freight.start_dispatch",
    )

    batch = dispatch_order.batch

    _check_branch_access(
        user=rejected_by,
        branch_id=batch.branch_id,
    )

    if batch.status != DispatchBatch.Status.IN_PROGRESS:
        raise ValidationError(
            "A dispatch order can only be rejected "
            "while the batch is in progress."
        )

    if dispatch_order.status != DispatchOrder.Status.IN_PROGRESS:
        raise ValidationError(
            "Only in-progress dispatch orders can be rejected."
        )

    if not reason.strip():
        raise ValidationError(
            "A rejection reason is required."
        )

    active_assignment = dispatch_order.freight_assignments.filter(
        status=DispatchFreightAssignment.Status.DISPATCHING
    ).exists()

    if active_assignment:
        raise ValidationError(
            "The active freight assignment must be rejected "
            "or cancelled before rejecting the dispatch order."
        )

    dispatch_order.status = DispatchOrder.Status.REJECTED

    dispatch_order.notes = reason

    if notes:
        dispatch_order.notes = (
            f"{reason}\n{notes}"
        )

    dispatch_order.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    return dispatch_order


@transaction.atomic
def return_dispatch_order(           
    *,
    dispatch_order,
    returned_by,
    notes="",
):
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

    if batch.status != DispatchBatch.Status.COMPLETED:
        raise ValidationError(
            "An order can only be returned after "
            "the dispatch batch is completed."
        )

    if dispatch_order.status != DispatchOrder.Status.REJECTED:
        raise ValidationError(
            "Only rejected dispatch orders can be returned."
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

    old_status = order.status

    if order.status != ShipmentOrder.Status.READY_FOR_DISPATCH:
        order.status = ShipmentOrder.Status.READY_FOR_DISPATCH

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        ShipmentStatusHistory.objects.create(
            shipment=order,
            from_status=old_status,
            to_status=ShipmentOrder.Status.READY_FOR_DISPATCH,
            changed_by=returned_by,
            note=notes,
        )

    return dispatch_order


@transaction.atomic
def complete_dispatch_batch(                        
    *,
    batch,
    completed_by,
):
    _check_dispatch_permission(
        user=completed_by,
        permission="freight.complete_dispatch",
    )

    _check_branch_access(
        user=completed_by,
        branch_id=batch.branch_id,
    )

    _validate_transition(
        current_status=batch.status,
        new_status=DispatchBatch.Status.COMPLETED,
        transitions=BATCH_TRANSITIONS,
    )

    dispatch_orders = batch.orders.select_for_update().all()

    if not dispatch_orders.exists():
        raise ValidationError(
            "A dispatch batch must contain at least one order."
        )

    unfinished_orders = dispatch_orders.exclude(
        status__in={
            DispatchOrder.Status.DELIVERED,
            DispatchOrder.Status.REJECTED,
        }
    )

    if unfinished_orders.exists():
        raise ValidationError(
            "All dispatch orders must be delivered or rejected "
            "before the batch can be completed."
        )

    now = timezone.now()

    batch.status = DispatchBatch.Status.COMPLETED
    batch.completed_at = now

    batch.save(
        update_fields=[
            "status",
            "completed_at",
            "updated_at",
        ]
    )

    return batch


@transaction.atomic
def cancel_dispatch_batch(
    *,
    batch,
    cancelled_by,
    notes="",
):
    _check_dispatch_permission(
        user=cancelled_by,
        permission="freight.change_dispatchbatch",
    )

    _check_branch_access(
        user=cancelled_by,
        branch_id=batch.branch_id,
    )

    _validate_transition(
        current_status=batch.status,
        new_status=DispatchBatch.Status.CANCELLED,
        transitions=BATCH_TRANSITIONS,
    )

    if batch.status == DispatchBatch.Status.IN_PROGRESS:
        active_orders = batch.orders.filter(
            status=DispatchOrder.Status.IN_PROGRESS
        ).exists()

        if active_orders:
            raise ValidationError(
                "An in-progress batch cannot be cancelled while "
                "dispatch orders are still in progress."
            )

    batch.status = DispatchBatch.Status.CANCELLED

    if notes:
        batch.notes = notes

    batch.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    return batch


@transaction.atomic
def cancel_dispatch_order(
    *,
    dispatch_order,
    cancelled_by,
    notes="",
):
    _check_dispatch_permission(
        user=cancelled_by,
        permission="freight.change_dispatchbatch",
    )

    batch = dispatch_order.batch
    order = dispatch_order.order

    _check_branch_access(
        user=cancelled_by,
        branch_id=batch.branch_id,
    )

    if dispatch_order.status not in {
        DispatchOrder.Status.PENDING,
        DispatchOrder.Status.IN_PROGRESS,
        DispatchOrder.Status.REJECTED,
    }:
        raise ValidationError(
            "This dispatch order cannot be cancelled "
            "in its current status."
        )

    active_assignment = dispatch_order.freight_assignments.filter(
        status__in={
            DispatchFreightAssignment.Status.DISPATCHING,
            DispatchFreightAssignment.Status.PENDING_APPROVAL,
        }
    ).exists()

    if active_assignment:
        raise ValidationError(
            "The active freight assignment must be cancelled "
            "before cancelling the dispatch order."
        )

    dispatch_order.status = DispatchOrder.Status.CANCELLED

    if notes:
        dispatch_order.notes = notes

    dispatch_order.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    old_status = order.status

    if order.status != ShipmentOrder.Status.CANCELLED:
        order.status = ShipmentOrder.Status.CANCELLED

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        ShipmentStatusHistory.objects.create(
            shipment=order,
            from_status=old_status,
            to_status=ShipmentOrder.Status.CANCELLED,
            changed_by=cancelled_by,
            note=notes,
        )

    return dispatch_order


@transaction.atomic
def cancel_freight_assignment(
    *,
    assignment,
    cancelled_by,
    notes="",
):
    _check_dispatch_permission(
        user=cancelled_by,
        permission="freight.change_dispatchbatch",
    )

    dispatch_order = assignment.dispatch_order
    batch = dispatch_order.batch

    _check_branch_access(
        user=cancelled_by,
        branch_id=batch.branch_id,
    )

    if assignment.status not in {
        DispatchFreightAssignment.Status.DISPATCHING,
        DispatchFreightAssignment.Status.PENDING_APPROVAL,
    }:
        raise ValidationError(
            "This freight assignment cannot be cancelled "
            "in its current status."
        )

    if assignment.status == (
        DispatchFreightAssignment.Status.PENDING_APPROVAL
    ):
        raise ValidationError(
            "A freight assignment pending approval cannot "
            "be cancelled."
        )

    assignment.status = DispatchFreightAssignment.Status.CANCELLED

    if notes:
        assignment.notes = notes

    assignment.save(
        update_fields=[
            "status",
            "notes",
            "updated_at",
        ]
    )

    return assignment