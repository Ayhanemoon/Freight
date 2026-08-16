from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from freight.models import CollectionTask, Parcel


ALLOWED_TRANSITIONS = {
    CollectionTask.Status.PENDING: {
        CollectionTask.Status.ASSIGNED,
        CollectionTask.Status.CANCELLED,
    },
    CollectionTask.Status.ASSIGNED: {
        CollectionTask.Status.IN_PROGRESS,
        CollectionTask.Status.CANCELLED,
    },
    CollectionTask.Status.IN_PROGRESS: {
        CollectionTask.Status.COMPLETED,
        CollectionTask.Status.FAILED,
        CollectionTask.Status.CANCELLED,
    },
    CollectionTask.Status.COMPLETED: set(),
    CollectionTask.Status.CANCELLED: set(),
    CollectionTask.Status.FAILED: set(),
}


def assign_collector(*, task, collector):
    """
    Assign a CargoCollector to a collection task.

    Authorization is handled by the API permission layer.
    This function only validates business rules.
    """

    if task.status != CollectionTask.Status.PENDING:
        raise ValidationError(
            "Only pending collection tasks can be assigned."
        )

    if not collector.is_active:
        raise ValidationError(
            "Selected collector is not active."
        )

    if not collector.groups.filter(
        name="CargoCollector"
    ).exists():
        raise ValidationError(
            "Selected user is not a Cargo Collector."
        )

    if collector.branch_id != task.order.branch_id:
        raise ValidationError(
            "Collector must belong to the same branch as the order."
        )

    task.collector = collector
    task.status = CollectionTask.Status.ASSIGNED

    task.save(
        update_fields=[
            "collector",
            "status",
            "updated_at",
        ]
    )

    return task


def change_collection_status(
    *,
    task,
    new_status,
    user,
    note="",
):
    """
    Change the status of a collection task.

    Authorization is handled by the API permission layer.
    This function validates state transitions and business rules.
    """

    current_status = task.status

    if current_status == new_status:
        raise ValidationError(
            f"Collection task is already {current_status}."
        )

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValidationError(
            f"Cannot change collection task from "
            f"{current_status} to {new_status}."
        )

    if new_status in {
        CollectionTask.Status.IN_PROGRESS,
        CollectionTask.Status.COMPLETED,
        CollectionTask.Status.FAILED,
    }:
        if task.collector_id != user.id:
            raise ValidationError(
                "You can only operate on collection tasks assigned to you."
            )

        if user.branch_id != task.order.branch_id:
            raise ValidationError(
                "Collector and order must belong to the same branch."
            )

    elif new_status in {
        CollectionTask.Status.ASSIGNED,
        CollectionTask.Status.CANCELLED,
    }:
        if user.branch_id != task.order.branch_id:
            raise ValidationError(
                "You cannot manage collection tasks outside your branch."
            )

    now = timezone.now()

    task.status = new_status

    update_fields = [
        "status",
        "updated_at",
    ]

    if new_status == CollectionTask.Status.IN_PROGRESS:
        task.started_at = now
        update_fields.append("started_at")

    elif new_status == CollectionTask.Status.COMPLETED:
        task.completed_at = now
        update_fields.append("completed_at")

    if note:
        task.notes = note
        update_fields.append("notes")

    task.save(update_fields=update_fields)

    return task

@transaction.atomic
def verify_parcel(
    *,
    task,
    parcel,
    verified_by,
    weight_kg,
    length_cm,
    width_cm,
    height_cm,
):
    if task.status not in {
        CollectionTask.Status.ASSIGNED,
        CollectionTask.Status.IN_PROGRESS,
    }:
        raise ValidationError(
            "Parcels can only be verified for an active collection task."
        )

    if task.collector_id != verified_by.id:
        raise ValidationError(
            "You can only verify parcels assigned to you."
        )

    if parcel.order_id != task.order_id:
        raise ValidationError(
            "This parcel does not belong to this collection task."
        )

    if weight_kg <= 0:
        raise ValidationError(
            "Weight must be greater than zero."
        )

    if length_cm <= 0:
        raise ValidationError(
            "Length must be greater than zero."
        )

    if width_cm <= 0:
        raise ValidationError(
            "Width must be greater than zero."
        )

    if height_cm <= 0:
        raise ValidationError(
            "Height must be greater than zero."
        )

    now = timezone.now()

    # Store physical verification values.
    parcel.verified_weight_kg = weight_kg
    parcel.verified_length_cm = length_cm
    parcel.verified_width_cm = width_cm
    parcel.verified_height_cm = height_cm

    parcel.verified_by = verified_by
    parcel.verified_at = now

    # Check whether the physical values differ
    # from the customer's declaration.
    has_difference = (
        parcel.declared_weight_kg != weight_kg
        or parcel.declared_length_cm != length_cm
        or parcel.declared_width_cm != width_cm
        or parcel.declared_height_cm != height_cm
    )

    if has_difference:
        parcel.verification_status = (
            Parcel.VerificationStatus.DIFFERENCE_FOUND
        )
    else:
        parcel.verification_status = (
            Parcel.VerificationStatus.VERIFIED
        )

    parcel.save(
        update_fields=[
            "verified_weight_kg",
            "verified_length_cm",
            "verified_width_cm",
            "verified_height_cm",
            "verification_status",
            "verified_by",
            "verified_at",
            "updated_at",
        ]
    )

    # The collector has started the physical collection
    # once the first parcel is verified.
    if task.status == CollectionTask.Status.ASSIGNED:
        task.status = CollectionTask.Status.IN_PROGRESS
        task.started_at = now

        task.save(
            update_fields=[
                "status",
                "started_at",
                "updated_at",
            ]
        )

    return parcel

@transaction.atomic
def complete_collection(
    *,
    task,
    completed_by,
):
    if task.status != CollectionTask.Status.IN_PROGRESS:
        raise ValidationError(
            "Only an in-progress collection task can be completed."
        )

    if task.collector_id != completed_by.id:
        raise ValidationError(
            "You can only complete collection tasks assigned to you."
        )

    parcels = task.order.parcels.all()

    if not parcels.exists():
        raise ValidationError(
            "The order must contain at least one parcel."
        )

    unverified_parcels = parcels.filter(
        verification_status=Parcel.VerificationStatus.PENDING
    )

    if unverified_parcels.exists():
        raise ValidationError(
            "All parcels must be verified before completing collection."
        )

    now = timezone.now()

    task.status = CollectionTask.Status.COMPLETED
    task.completed_at = now

    task.save(
        update_fields=[
            "status",
            "completed_at",
            "updated_at",
        ]
    )

    return task

