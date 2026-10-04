from django.db import IntegrityError
from rest_framework.exceptions import PermissionDenied, ValidationError

from freight.models import CustomerBranchMembership
from freight.tests.base import FreightAPITestCase

from freight.services.customer_branch_membership import (
    request_customer_branch_membership,
)


class CustomerBranchMembershipModelTests(FreightAPITestCase):

    def test_customer_can_have_multiple_active_branch_memberships(self):
        customer_user = self.create_user(
            mobile="09120000001",
        )

        customer = self.create_customer(
            user=customer_user,
        )

        tehran = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        mashhad = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        first = CustomerBranchMembership.objects.create(
            customer=customer,
            branch=tehran,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        second = CustomerBranchMembership.objects.create(
            customer=customer,
            branch=mashhad,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            customer.branch_memberships.count(),
            2,
        )

        self.assertEqual(
            first.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            second.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

    def test_customer_cannot_have_duplicate_membership_for_same_branch(self):
        customer_user = self.create_user(
            mobile="09120000002",
        )

        customer = self.create_customer(
            user=customer_user,
        )

        branch = self.create_branch()

        CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        with self.assertRaises(IntegrityError):
            CustomerBranchMembership.objects.create(
                customer=customer,
                branch=branch,
                status=CustomerBranchMembership.Status.ACTIVE,
            )

class CustomerBranchMembershipServiceTests(FreightAPITestCase):

    def setUp(self):
        self.customer_user = self.create_user(
            mobile="09121111101",
        )

        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.tehran = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.mashhad = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

    def test_customer_can_request_branch_membership(self):
        membership = request_customer_branch_membership(
            user=self.customer_user,
            branch=self.tehran,
        )

        self.assertEqual(
            membership.customer_id,
            self.customer.id,
        )
        self.assertEqual(
            membership.branch_id,
            self.tehran.id,
        )
        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )
        self.assertIsNone(membership.approved_at)
        self.assertIsNone(membership.approved_by)

    def test_customer_cannot_directly_create_active_membership(self):
        membership = request_customer_branch_membership(
            user=self.customer_user,
            branch=self.tehran,
        )

        self.assertNotEqual(
            membership.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

    def test_customer_can_request_multiple_branches(self):
        first = request_customer_branch_membership(
            user=self.customer_user,
            branch=self.tehran,
        )

        second = request_customer_branch_membership(
            user=self.customer_user,
            branch=self.mashhad,
        )

        self.assertEqual(
            first.status,
            CustomerBranchMembership.Status.PENDING,
        )
        self.assertEqual(
            second.status,
            CustomerBranchMembership.Status.PENDING,
        )

        self.assertEqual(
            self.customer.branch_memberships.count(),
            2,
        )

    def test_customer_cannot_request_same_branch_twice(self):
        request_customer_branch_membership(
            user=self.customer_user,
            branch=self.tehran,
        )

        with self.assertRaises(ValidationError):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )

        self.assertEqual(
            self.customer.branch_memberships.filter(
                branch=self.tehran,
            ).count(),
            1,
        )

    def test_inactive_branch_cannot_be_requested(self):
        self.tehran.is_active = False
        self.tehran.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )

        self.assertFalse(
            self.customer.branch_memberships.filter(
                branch=self.tehran,
            ).exists()
        )

    def test_user_without_customer_profile_cannot_request_membership(self):
        user = self.create_user(
            mobile="09121111102",
        )

        with self.assertRaises(PermissionDenied):
            request_customer_branch_membership(
                user=user,
                branch=self.tehran,
            )

    def test_inactive_user_cannot_request_membership(self):
        self.customer_user.is_active = False
        self.customer_user.save(update_fields=["is_active"])

        with self.assertRaises(PermissionDenied):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )

    def test_unauthenticated_user_cannot_request_membership(self):
        with self.assertRaises(PermissionDenied):
            request_customer_branch_membership(
                user=None,
                branch=self.tehran,
            )

    def test_membership_always_belongs_to_authenticated_users_customer(self):
        other_user = self.create_user(
            mobile="09121111103",
        )

        other_customer = self.create_customer(
            user=other_user,
        )

        membership = request_customer_branch_membership(
            user=self.customer_user,
            branch=self.tehran,
        )

        self.assertEqual(
            membership.customer_id,
            self.customer.id,
        )
        self.assertNotEqual(
            membership.customer_id,
            other_customer.id,
        )

    def test_existing_active_membership_cannot_be_requested_again(self):
        CustomerBranchMembership.objects.create(
            customer=self.customer,
            branch=self.tehran,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        with self.assertRaises(ValidationError):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )

    def test_existing_suspended_membership_cannot_be_requested_again(self):
        CustomerBranchMembership.objects.create(
            customer=self.customer,
            branch=self.tehran,
            status=CustomerBranchMembership.Status.SUSPENDED,
        )

        with self.assertRaises(ValidationError):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )

    def test_existing_ended_membership_cannot_be_requested_again(self):
        CustomerBranchMembership.objects.create(
            customer=self.customer,
            branch=self.tehran,
            status=CustomerBranchMembership.Status.ENDED,
        )

        with self.assertRaises(ValidationError):
            request_customer_branch_membership(
                user=self.customer_user,
                branch=self.tehran,
            )