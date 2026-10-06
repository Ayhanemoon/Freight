import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import (
    Customer,
    CustomerRegistrationInvitation,
)
from freight.services.customer_onboarding import onboard_customer
from freight.permissions.capabilities import (
    has_branch_admin_capability,
)


TOKEN_BYTES = 32
DEFAULT_INVITATION_LIFETIME = timedelta(days=7)
User = get_user_model()


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_token():
    return secrets.token_urlsafe(TOKEN_BYTES)


def _validate_invitation_creator(user, branch):
    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required to create an invitation."
        )

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    if not has_branch_admin_capability(user):
        raise PermissionDenied(
            "You do not have permission to create customer invitations."
        )

    if not user.is_superuser and user.branch_id != branch.id:
        raise PermissionDenied(
            "You cannot create an invitation for another branch."
        )


def _validate_target(*, customer=None, target_mobile=None):
    if customer is not None and target_mobile is not None:
        raise ValidationError(
            "Invitation cannot target both a customer and a mobile number."
        )


def create_customer_registration_invitation(
    *,
    user,
    branch,
    customer=None,
    target_mobile=None,
    expires_at=None,
    max_uses=1,
):
    """
    Create a customer registration invitation.

    Returns:
        tuple: (invitation, raw_token)
    """
    _validate_invitation_creator(user, branch)

    if not branch.is_active:
        raise ValidationError(
            "Cannot create an invitation for an inactive branch."
        )

    _validate_target(
        customer=customer,
        target_mobile=target_mobile,
    )

    if customer is not None:
        if not Customer.objects.filter(
            pk=customer.pk
        ).exists():
            raise ValidationError(
                "Customer does not exist."
            )

        if customer.user_id is None:
            raise ValidationError(
                "Customer must have a user account."
            )

    if max_uses <= 0:
        raise ValidationError(
            "max_uses must be greater than zero."
        )

    if expires_at is None:
        expires_at = timezone.now() + DEFAULT_INVITATION_LIFETIME

    if expires_at <= timezone.now():
        raise ValidationError(
            "Invitation expiration must be in the future."
        )

    token = _generate_token()
    token_hash = _hash_token(token)

    invitation = CustomerRegistrationInvitation.objects.create(
        branch=branch,
        token_hash=token_hash,
        created_by=user,
        customer=customer,
        target_mobile=target_mobile,
        expires_at=expires_at,
        max_uses=max_uses,
    )

    return invitation, token


def get_valid_customer_registration_invitation(token):
    """
    Return a valid invitation for a raw token.

    This does not consume the invitation.
    """
    token_hash = _hash_token(token)

    invitation = (
        CustomerRegistrationInvitation.objects
        .select_for_update()
        .select_related(
            "branch",
            "customer",
            "customer__user",
        )
        .filter(token_hash=token_hash)
        .first()
    )

    if invitation is None:
        raise ValidationError(
            "Invalid invitation."
        )

    if invitation.revoked_at is not None:
        raise ValidationError(
            "Invitation has been revoked."
        )

    if invitation.expires_at <= timezone.now():
        raise ValidationError(
            "Invitation has expired."
        )

    if invitation.used_count >= invitation.max_uses:
        raise ValidationError(
            "Invitation has reached its usage limit."
        )

    if not invitation.branch.is_active:
        raise ValidationError(
            "Invitation branch is inactive."
        )

    return invitation


def consume_customer_registration_invitation(
    *,
    token,
    user,
):
    """
    Atomically consume one invitation use.

    The invitation is locked during the transaction so that
    one-time invitations cannot be consumed concurrently.
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required to consume an invitation."
        )

    if not user.is_active:
        raise PermissionDenied(
            "User account is inactive."
        )

    token_hash = _hash_token(token)

    with transaction.atomic():
        invitation = (
            CustomerRegistrationInvitation.objects
            .select_for_update()
            .select_related(
                "branch",
                "customer",
                "customer__user",
            )
            .filter(token_hash=token_hash)
            .first()
        )

        if invitation is None:
            raise ValidationError(
                "Invalid invitation."
            )

        if invitation.revoked_at is not None:
            raise ValidationError(
                "Invitation has been revoked."
            )

        if invitation.expires_at <= timezone.now():
            raise ValidationError(
                "Invitation has expired."
            )

        if invitation.used_count >= invitation.max_uses:
            raise ValidationError(
                "Invitation has reached its usage limit."
            )

        if not invitation.branch.is_active:
            raise ValidationError(
                "Invitation branch is inactive."
            )

        if invitation.customer_id is not None:
            if invitation.customer.user_id != user.id:
                raise PermissionDenied(
                    "This invitation is not intended for this customer."
                )

        if invitation.target_mobile is not None:
            normalized_target_mobile = User.objects.normalize_mobile(
                invitation.target_mobile
            )

            normalized_user_mobile = User.objects.normalize_mobile(
                user.mobile
            )

            if normalized_user_mobile != normalized_target_mobile:
                raise PermissionDenied(
                    "This invitation is not intended for this mobile number."
                )

        invitation.used_count += 1
        invitation.save(
            update_fields=["used_count"]
        )

        return invitation


def revoke_customer_registration_invitation(
    *,
    user,
    invitation_id,
):
    """
    Revoke an invitation without deleting its audit history.
    """
    with transaction.atomic():
        invitation = (
            CustomerRegistrationInvitation.objects
            .select_for_update()
            .select_related("branch")
            .filter(pk=invitation_id)
            .first()
        )

        if invitation is None:
            raise ValidationError(
                "Invitation not found."
            )

        _validate_invitation_creator(
            user,
            invitation.branch,
        )

        if invitation.revoked_at is not None:
            return invitation

        invitation.revoked_at = timezone.now()
        invitation.save(
            update_fields=["revoked_at"]
        )

        return invitation


def register_customer_with_invitation(
    *,
    invitation_token,
    mobile,
    password,
    customer_type,
    first_name="",
    last_name="",
    national_id="",
    company_name="",
    company_registration_no="",
    economic_code="",
):
    """
    Register a new customer through a branch invitation.

    The invitation determines the customer's branch.
    The client cannot choose the branch.

    Returns:
        tuple: (user, customer, membership, invitation)
    """

    normalized_mobile = User.objects.normalize_mobile(
        mobile
    )

    with transaction.atomic():
        invitation = get_valid_customer_registration_invitation(
            invitation_token
        )

        if invitation.customer_id is not None:
            raise ValidationError(
                "This invitation is for an existing customer."
            )

        if invitation.target_mobile is not None:
            normalized_target_mobile = User.objects.normalize_mobile(
                invitation.target_mobile
            )

            if normalized_mobile != normalized_target_mobile:
                raise PermissionDenied(
                    "This invitation is not intended for this mobile number."
                )

        if User.objects.filter(
            mobile=normalized_mobile
        ).exists():
            raise ValidationError(
                "A user with this mobile number already exists."
            )

        user = User.objects.create_user(
            mobile=normalized_mobile,
            password=password,
            auth_provider="mobile",
        )

        customer, membership = onboard_customer(
            user=user,
            customer_type=customer_type,
            first_name=first_name,
            last_name=last_name,
            national_id=national_id,
            company_name=company_name,
            company_registration_no=company_registration_no,
            economic_code=economic_code,
            branch=invitation.branch,
        )

        invitation.used_count += 1
        invitation.save(
            update_fields=["used_count"]
        )

        return (
            user,
            customer,
            membership,
            invitation,
        )