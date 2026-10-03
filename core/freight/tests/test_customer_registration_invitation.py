from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from freight.models import CustomerRegistrationInvitation
from freight.tests.base import FreightAPITestCase


class CustomerRegistrationInvitationModelTests(FreightAPITestCase):

    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.user = self.create_user(
            mobile="09121111111",
            branch=self.branch,
            is_staff=True,
        )

        self.customer = self.create_customer(
            user=self.create_user(
                mobile="09122222222",
                is_mobile_verified=True,
            ),
        )

    def test_create_generic_invitation(self):
        invitation = CustomerRegistrationInvitation.objects.create(
            branch=self.branch,
            token_hash="a" * 64,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(days=1),
        )

        self.assertIsNone(invitation.customer)
        self.assertIsNone(invitation.target_mobile)
        self.assertEqual(invitation.max_uses, 1)
        self.assertEqual(invitation.used_count, 0)
        self.assertIsNone(invitation.revoked_at)

    def test_create_customer_specific_invitation(self):
        invitation = CustomerRegistrationInvitation.objects.create(
            branch=self.branch,
            token_hash="b" * 64,
            created_by=self.user,
            customer=self.customer,
            expires_at=timezone.now() + timedelta(days=1),
        )

        self.assertEqual(
            invitation.customer_id,
            self.customer.id,
        )
        self.assertIsNone(invitation.target_mobile)

    def test_create_mobile_specific_invitation(self):
        invitation = CustomerRegistrationInvitation.objects.create(
            branch=self.branch,
            token_hash="c" * 64,
            created_by=self.user,
            target_mobile="09123333333",
            expires_at=timezone.now() + timedelta(days=1),
        )

        self.assertIsNone(invitation.customer)
        self.assertEqual(
            str(invitation.target_mobile),
            "09123333333",
        )

    def test_customer_and_target_mobile_cannot_both_be_set(self):
        invitation = CustomerRegistrationInvitation(
            branch=self.branch,
            token_hash="d" * 64,
            created_by=self.user,
            customer=self.customer,
            target_mobile="09124444444",
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            invitation.full_clean()

    def test_max_uses_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            CustomerRegistrationInvitation.objects.create(
                branch=self.branch,
                token_hash="e" * 64,
                created_by=self.user,
                max_uses=0,
                expires_at=timezone.now() + timedelta(days=1),
            )

    def test_used_count_cannot_exceed_max_uses(self):
        with self.assertRaises(IntegrityError):
            CustomerRegistrationInvitation.objects.create(
                branch=self.branch,
                token_hash="f" * 64,
                created_by=self.user,
                max_uses=1,
                used_count=2,
                expires_at=timezone.now() + timedelta(days=1),
            )

    def test_token_hash_must_be_unique(self):
        CustomerRegistrationInvitation.objects.create(
            branch=self.branch,
            token_hash="g" * 64,
            created_by=self.user,
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(IntegrityError):
            CustomerRegistrationInvitation.objects.create(
                branch=self.branch,
                token_hash="g" * 64,
                created_by=self.user,
                expires_at=timezone.now() + timedelta(days=1),
            )