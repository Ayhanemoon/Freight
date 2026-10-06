from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import (
    Customer,
    CustomerBranchMembership,
)
from freight.constants.roles import Roles
from freight.models import CustomerRegistrationInvitation
from freight.services.customer_registration_invitation import (
    create_customer_registration_invitation,
    consume_customer_registration_invitation,
    get_valid_customer_registration_invitation,
    revoke_customer_registration_invitation,
    register_customer_with_invitation,
)
from freight.tests.base import FreightAPITestCase

User = get_user_model()

class CustomerRegistrationInvitationServiceTests(FreightAPITestCase):

    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Karaj Branch",
            code="KRJ",
            city="Karaj",
        )

        self.manager = self.create_user(
            mobile="09121111111",
            branch=self.branch,
            is_staff=True,
        )

        self.manager_group = Group.objects.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.manager.groups.add(self.manager_group)

        self.other_manager = self.create_user(
            mobile="09121111112",
            branch=self.other_branch,
            is_staff=True,
        )

        self.other_manager.groups.add(self.manager_group)

        self.customer_user = self.create_user(
            mobile="09122222222",
            is_mobile_verified=True,
        )

        self.customer = self.create_customer(
            user=self.customer_user,
        )

    def test_create_invitation_generates_raw_token_and_stores_only_hash(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        self.assertTrue(token)
        self.assertGreaterEqual(len(token), 40)

        self.assertNotEqual(
            invitation.token_hash,
            token,
        )

        self.assertEqual(
            invitation.used_count,
            0,
        )

        self.assertEqual(
            invitation.max_uses,
            1,
        )

    def test_create_invitation_default_expiration(self):
        before = timezone.now() + timedelta(days=7)

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        after = timezone.now() + timedelta(days=7)

        self.assertGreaterEqual(
            invitation.expires_at,
            before,
        )
        self.assertLessEqual(
            invitation.expires_at,
            after,
        )

    def test_create_invitation_with_custom_expiration(self):
        expires_at = timezone.now() + timedelta(days=30)

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                expires_at=expires_at,
            )
        )

        self.assertEqual(
            invitation.expires_at,
            expires_at,
        )

    def test_branch_manager_cannot_create_for_other_branch(self):
        with self.assertRaises(PermissionDenied):
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.other_branch,
            )

    def test_non_manager_cannot_create_invitation(self):
        user = self.create_user(
            mobile="09123333333",
            branch=self.branch,
            is_staff=True,
        )

        with self.assertRaises(PermissionDenied):
            create_customer_registration_invitation(
                user=user,
                branch=self.branch,
            )

    def test_inactive_branch_cannot_create_invitation(self):
        self.branch.is_active = False
        self.branch.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )

    def test_customer_specific_invitation(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                customer=self.customer,
            )
        )

        self.assertEqual(
            invitation.customer_id,
            self.customer.id,
        )

        valid = get_valid_customer_registration_invitation(
            token,
        )

        self.assertEqual(
            valid.id,
            invitation.id,
        )

    def test_mobile_specific_invitation(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                target_mobile="09123333333",
            )
        )

        self.assertEqual(
            str(invitation.target_mobile),
            "09123333333",
        )

        valid = get_valid_customer_registration_invitation(
            token,
        )

        self.assertEqual(
            valid.id,
            invitation.id,
        )

    def test_customer_and_mobile_cannot_both_be_used(self):
        with self.assertRaises(ValidationError):
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                customer=self.customer,
                target_mobile="09123333333",
            )

    def test_expired_invitation_is_invalid(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                expires_at=timezone.now() + timedelta(seconds=1),
            )
        )

        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])

        with self.assertRaises(ValidationError):
            get_valid_customer_registration_invitation(
                token,
            )

    def test_revoked_invitation_is_invalid(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        revoke_customer_registration_invitation(
            user=self.manager,
            invitation_id=invitation.id,
        )

        with self.assertRaises(ValidationError):
            get_valid_customer_registration_invitation(
                token,
            )

    def test_exhausted_invitation_is_invalid(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                max_uses=1,
            )
        )

        invitation.used_count = 1
        invitation.save(update_fields=["used_count"])

        with self.assertRaises(ValidationError):
            get_valid_customer_registration_invitation(
                token,
            )

    def test_customer_specific_invitation_rejects_wrong_user(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                customer=self.customer,
            )
        )

        another_user = self.create_user(
            mobile="09123333333",
            is_mobile_verified=True,
        )

        with self.assertRaises(PermissionDenied):
            consume_customer_registration_invitation(
                token=token,
                user=another_user,
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_mobile_specific_invitation_rejects_wrong_mobile(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                target_mobile="09123333333",
            )
        )

        wrong_user = self.create_user(
            mobile="09124444444",
            is_mobile_verified=True,
        )

        with self.assertRaises(PermissionDenied):
            consume_customer_registration_invitation(
                token=token,
                user=wrong_user,
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_customer_specific_invitation_can_be_consumed_by_owner(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                customer=self.customer,
            )
        )

        consumed = consume_customer_registration_invitation(
            token=token,
            user=self.customer_user,
        )

        self.assertEqual(
            consumed.id,
            invitation.id,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_mobile_specific_invitation_can_be_consumed_by_target(self):
        target_user = self.create_user(
            mobile="09123333333",
            is_mobile_verified=True,
        )

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                target_mobile="09123333333",
            )
        )

        consumed = consume_customer_registration_invitation(
            token=token,
            user=target_user,
        )

        self.assertEqual(
            consumed.id,
            invitation.id,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_one_time_invitation_cannot_be_consumed_twice(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        self.create_user(
            mobile="09123333333",
            is_mobile_verified=True,
        )

        # Generic invitations don't have a target, so the authenticated
        # user can consume them.
        user = self.create_user(
            mobile="09124444444",
            is_mobile_verified=True,
        )

        consume_customer_registration_invitation(
            token=token,
            user=user,
        )

        with self.assertRaises(ValidationError):
            consume_customer_registration_invitation(
                token=token,
                user=user,
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_multi_use_invitation_can_be_consumed_until_limit(self):
        user_one = self.create_user(
            mobile="09123333333",
            is_mobile_verified=True,
        )

        user_two = self.create_user(
            mobile="09124444444",
            is_mobile_verified=True,
        )

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                max_uses=2,
            )
        )

        consume_customer_registration_invitation(
            token=token,
            user=user_one,
        )

        consume_customer_registration_invitation(
            token=token,
            user=user_two,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            2,
        )

        with self.assertRaises(ValidationError):
            consume_customer_registration_invitation(
                token=token,
                user=user_one,
            )

    def test_inactive_branch_invitation_cannot_be_consumed(self):
        user = self.create_user(
            mobile="09123333333",
            is_mobile_verified=True,
        )

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        self.branch.is_active = False
        self.branch.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            consume_customer_registration_invitation(
                token=token,
                user=user,
            )

    def test_revoke_is_idempotent(self):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
            )
        )

        first = revoke_customer_registration_invitation(
            user=self.manager,
            invitation_id=invitation.id,
        )

        second = revoke_customer_registration_invitation(
            user=self.manager,
            invitation_id=invitation.id,
        )

        self.assertEqual(
            first.id,
            second.id,
        )

        invitation.refresh_from_db()

        self.assertIsNotNone(
            invitation.revoked_at,
        )


class CustomerRegistrationInvitationRegistrationTests(
    FreightAPITestCase
):

    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.manager = self.create_user(
            mobile="09129999991",
            branch=self.branch,
            is_staff=True,
        )

        self.manager_group = Group.objects.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.manager.groups.add(self.manager_group)

    def create_invitation(
        self,
        target_mobile=None,
    ):
        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                target_mobile=target_mobile,
            )
        )

        return invitation, token

    def test_customer_can_register_with_generic_invitation(self):
        invitation, token = self.create_invitation()

        user, customer, membership, returned_invitation = (
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111111",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )
        )

        self.assertIsNotNone(user)
        self.assertEqual(
            str(user.mobile),
            "+989121111111",
        )

        self.assertEqual(
            customer.user_id,
            user.id,
        )

        self.assertEqual(
            membership.branch_id,
            self.branch.id,
        )

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

        self.assertEqual(
            returned_invitation.id,
            invitation.id,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_customer_can_register_with_mobile_specific_invitation(self):
        invitation, token = self.create_invitation(
            target_mobile="09121111112",
        )

        user, customer, membership, returned_invitation = (
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111112",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )
        )

        self.assertEqual(
            str(user.mobile),
            "+989121111112",
        )

        self.assertEqual(
            customer.user_id,
            user.id,
        )

        self.assertEqual(
            membership.branch_id,
            self.branch.id,
        )

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_mobile_specific_invitation_rejects_wrong_mobile(self):
        invitation, token = self.create_invitation(
            target_mobile="09121111113",
        )

        with self.assertRaises(PermissionDenied):
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111114",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

        self.assertFalse(
            User.objects.filter(
                mobile="09121111114",
            ).exists()
        )

    def test_customer_specific_invitation_cannot_be_used_for_new_registration(
        self,
    ):
        existing_user = self.create_user(
            mobile="09121111115",
        )

        existing_customer = self.create_customer(
            user=existing_user,
        )

        invitation, token = (
            create_customer_registration_invitation(
                user=self.manager,
                branch=self.branch,
                customer=existing_customer,
            )
        )

        with self.assertRaises(ValidationError):
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111116",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_existing_mobile_cannot_register_again(self):
        existing_user = self.create_user(
            mobile="09121111117",
        )

        invitation, token = self.create_invitation()

        with self.assertRaises(ValidationError):
            register_customer_with_invitation(
                invitation_token=token,
                mobile=str(existing_user.mobile),
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_invitation_branch_is_used_without_client_branch(self):
        other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        other_manager = self.create_user(
            mobile="09121111112",
            branch=other_branch,
            is_staff=True,
        )

        other_manager.groups.add(
            self.manager_group,
        )



        invitation, token = (
            create_customer_registration_invitation(
                user=other_manager,
                branch=other_branch,
            )
        )

        user, customer, membership, returned_invitation = (
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111118",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                national_id="0012345678",
            )
        )

        self.assertEqual(
            membership.branch_id,
            other_branch.id,
        )

        self.assertNotEqual(
            membership.branch_id,
            self.branch.id,
        )

    def test_registration_creates_company_customer(self):
        invitation, token = self.create_invitation()

        user, customer, membership, returned_invitation = (
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111119",
                password="test@123456",
                customer_type=Customer.CustomerType.COMPANY,
                company_name="Example Co",
                company_registration_no="123456",
                economic_code="987654321",
            )
        )

        self.assertEqual(
            customer.customer_type,
            Customer.CustomerType.COMPANY,
        )

        self.assertEqual(
            customer.company_name,
            "Example Co",
        )

        self.assertEqual(
            membership.branch_id,
            self.branch.id,
        )

    def test_failed_onboarding_does_not_consume_invitation_or_create_user(
        self,
    ):
        invitation, token = self.create_invitation()

        with self.assertRaises(ValidationError):
            register_customer_with_invitation(
                invitation_token=token,
                mobile="09121111120",
                password="test@123456",
                customer_type=Customer.CustomerType.PERSON,
                first_name="Ali",
                last_name="Ahmadi",
                # national_id intentionally missing
            )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

        self.assertFalse(
            User.objects.filter(
                mobile="09121111120",
            ).exists()
        )