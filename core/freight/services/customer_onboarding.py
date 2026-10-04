from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import (
    Customer,
    CustomerBranchMembership,
)


def _validate_customer_data(
    *,
    customer_type,
    first_name="",
    last_name="",
    national_id="",
    company_name="",
    company_registration_no="",
    economic_code="",
):
    if customer_type == Customer.CustomerType.PERSON:
        if not first_name or not last_name:
            raise ValidationError(
                "First name and last name are required for a person."
            )

        if not national_id:
            raise ValidationError(
                "National ID is required for a person."
            )

        if company_name or company_registration_no or economic_code:
            raise ValidationError(
                "Company fields cannot be provided for a person."
            )

    elif customer_type == Customer.CustomerType.COMPANY:
        if not company_name:
            raise ValidationError(
                "Company name is required for a company."
            )

        if first_name or last_name or national_id:
            raise ValidationError(
                "Person fields cannot be provided for a company."
            )

    else:
        raise ValidationError(
            "Invalid customer type."
        )


def onboard_customer(
    *,
    user,
    customer_type,
    first_name="",
    last_name="",
    national_id="",
    company_name="",
    company_registration_no="",
    economic_code="",
    branch=None,
):
    """
    Create the authenticated user's customer profile.

    If branch is supplied, create a PENDING branch membership.

    Returns:
        tuple: (customer, membership)
    """

    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required for customer onboarding."
        )

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    if hasattr(user, "customer_profile"):
        raise ValidationError(
            "Customer profile already exists."
        )

    _validate_customer_data(
        customer_type=customer_type,
        first_name=first_name,
        last_name=last_name,
        national_id=national_id,
        company_name=company_name,
        company_registration_no=company_registration_no,
        economic_code=economic_code,
    )

    with transaction.atomic():
        customer = Customer.objects.create(
            user=user,
            customer_type=customer_type,
            first_name=first_name,
            last_name=last_name,
            national_id=national_id,
            company_name=company_name,
            company_registration_no=company_registration_no,
            economic_code=economic_code,
        )

        membership = None

        if branch is not None:
            if not branch.is_active:
                raise ValidationError(
                    "Cannot request membership in an inactive branch."
                )

            membership = CustomerBranchMembership.objects.create(
                customer=customer,
                branch=branch,
                status=CustomerBranchMembership.Status.PENDING,
            )

        return customer, membership