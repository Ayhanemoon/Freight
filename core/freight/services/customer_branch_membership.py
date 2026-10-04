from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import (
    Branch,
    CustomerBranchMembership,
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