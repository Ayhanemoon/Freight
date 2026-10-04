from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import (
    Branch,
    CustomerBranchMembership,
)
from freight.permissions.capabilities import (
    has_branch_admin_capability,
)


def _validate_customer(user):
    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required to request branch membership."
        )

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    try:
        return user.customer_profile
    except AttributeError:
        raise PermissionDenied(
            "Customer profile is required to request branch membership."
        )


def request_customer_branch_membership(
    *,
    user,
    branch,
):
    """
    Create a PENDING branch membership for the authenticated customer.

    The customer is always derived from the authenticated user.
    The caller cannot choose another customer or create an ACTIVE
    membership directly.

    Returns:
        CustomerBranchMembership
    """

    customer = _validate_customer(user)

    if branch is None:
        raise ValidationError(
            "Branch is required."
        )

    if not isinstance(branch, Branch):
        raise ValidationError(
            "Invalid branch."
        )

    if not branch.is_active:
        raise ValidationError(
            "Cannot request membership in an inactive branch."
        )

    if CustomerBranchMembership.objects.filter(
        customer=customer,
        branch=branch,
    ).exists():
        raise ValidationError(
            "Customer already has a membership for this branch."
        )

    with transaction.atomic():
        membership = CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=CustomerBranchMembership.Status.PENDING,
        )

    return membership

def approve_customer_branch_membership(
    *,
    user,
    membership,
):
    """
    Approve a pending customer branch membership.

    SuperAdmin can approve memberships globally.
    BranchManager can approve memberships only
    within their own branch.

    Returns:
        CustomerBranchMembership
    """

    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required to approve branch membership."
        )

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    if not has_branch_admin_capability(user):
        raise PermissionDenied(
            "You do not have permission to approve branch memberships."
        )

    if membership is None:
        raise ValidationError(
            "Membership is required."
        )

    if not isinstance(
        membership,
        CustomerBranchMembership,
    ):
        raise ValidationError(
            "Invalid membership."
        )

    if (
        not user.is_superuser
        and membership.branch_id != user.branch_id
    ):
        raise PermissionDenied(
            "You cannot approve a membership outside your branch."
        )

    if membership.status != CustomerBranchMembership.Status.PENDING:
        raise ValidationError(
            "Only pending memberships can be approved."
        )

    if not membership.branch.is_active:
        raise ValidationError(
            "Cannot approve membership for an inactive branch."
        )

    with transaction.atomic():
        membership.status = (
            CustomerBranchMembership.Status.ACTIVE
        )
        membership.approved_at = timezone.now()
        membership.approved_by = user

        membership.save(
            update_fields=[
                "status",
                "approved_at",
                "approved_by",
            ]
        )

    return membership