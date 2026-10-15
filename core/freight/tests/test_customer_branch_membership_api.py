from django.urls import reverse
from rest_framework import status

from freight.constants import Roles
from freight.models import CustomerBranchMembership
from freight.tests.base import FreightAPITestCase


class CustomerBranchMembershipRequestAPITests(
    FreightAPITestCase
):

    def setUp(self):
        self.customer_user = self.create_user(
            mobile="09122222201",
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

        self.url = reverse(
            "freight:freight-api-v1:customer-branch-membership-request"
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_customer_can_request_branch_membership(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["branch"]["id"],
            self.tehran.id,
        )

        self.assertEqual(
            response.data["branch"]["name"],
            self.tehran.name,
        )

        self.assertEqual(
            response.data["status"],
            CustomerBranchMembership.Status.PENDING,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).count(),
            1,
        )

    def test_unauthenticated_user_cannot_request_membership(self):
        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_without_customer_profile_cannot_request_membership(
        self,
    ):
        user = self.create_user(
            mobile="09122222202",
        )

        self.authenticate(user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.exists()
        )

    def test_inactive_branch_cannot_be_requested(self):
        self.tehran.is_active = False
        self.tehran.save(
            update_fields=["is_active"]
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).exists()
        )

    def test_customer_cannot_request_same_branch_twice(self):
        self.authenticate(self.customer_user)

        first_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
                branch=self.tehran,
            ).count(),
            1,
        )

    def test_customer_can_request_multiple_branches(self):
        self.authenticate(self.customer_user)

        first_response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
            },
            format="json",
        )

        second_response = self.client.post(
            self.url,
            {
                "branch": self.mashhad.id,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
            ).count(),
            2,
        )

    def test_client_cannot_choose_customer(self):
        other_user = self.create_user(
            mobile="09122222203",
        )

        other_customer = self.create_customer(
            user=other_user,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
                "customer": other_customer.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        membership = CustomerBranchMembership.objects.get(
            customer=self.customer,
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

    def test_client_cannot_create_active_membership(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": self.tehran.id,
                "status": CustomerBranchMembership.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        membership = CustomerBranchMembership.objects.get(
            customer=self.customer,
            branch=self.tehran,
        )

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_invalid_branch_id_is_rejected(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {
                "branch": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            CustomerBranchMembership.objects.filter(
                customer=self.customer,
            ).exists()
        )

    def test_branch_is_required(self):
        self.authenticate(self.customer_user)

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

class CustomerBranchMembershipApproveAPITests(
    FreightAPITestCase
):

    def setUp(self):
        self.customer_user = self.create_user(
            mobile="09122222301",
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

        self.manager = self.create_user(
            mobile="09122222302",
            branch=self.tehran,
        )

        self.manager.groups.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.superadmin = self.create_user(
            mobile="09122222303",
            is_superuser=True,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def get_url(self, membership):
        return reverse(
            "freight:freight-api-v1:customer-branch-membership-approve",
            kwargs={
                "membership_id": membership.id,
            },
        )

    def create_pending_membership(self, branch):
        return CustomerBranchMembership.objects.create(
            customer=self.customer,
            branch=branch,
            status=CustomerBranchMembership.Status.PENDING,
        )

    def test_branch_manager_can_approve_membership(self):
        membership = self.create_pending_membership(
            self.tehran,
        )

        self.authenticate(self.manager)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            membership.id,
        )

        self.assertEqual(
            response.data["branch"]["id"],
            self.tehran.id,
        )

        self.assertEqual(
            response.data["status"],
            CustomerBranchMembership.Status.ACTIVE,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            membership.approved_by_id,
            self.manager.id,
        )

        self.assertIsNotNone(
            membership.approved_at,
        )

    def test_unauthenticated_user_cannot_approve_membership(self):
        membership = self.create_pending_membership(
            self.tehran,
        )

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_customer_cannot_approve_membership(self):
        membership = self.create_pending_membership(
            self.tehran,
        )

        self.authenticate(self.customer_user)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["code"],
            "NOT_FOUND",
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_branch_manager_cannot_approve_membership_from_other_branch(
        self,
    ):
        membership = self.create_pending_membership(
            self.mashhad,
        )

        self.authenticate(self.manager)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["code"],
            "NOT_FOUND",
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_superadmin_can_approve_membership_from_any_branch(self):
        membership = self.create_pending_membership(
            self.mashhad,
        )

        self.authenticate(self.superadmin)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["status"],
            CustomerBranchMembership.Status.ACTIVE,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.assertEqual(
            membership.approved_by_id,
            self.superadmin.id,
        )

        self.assertIsNotNone(
            membership.approved_at,
        )

    def test_active_membership_cannot_be_approved_again(self):
        membership = CustomerBranchMembership.objects.create(
            customer=self.customer,
            branch=self.tehran,
            status=CustomerBranchMembership.Status.ACTIVE,
        )

        self.authenticate(self.manager)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.ACTIVE,
        )

    def test_membership_for_inactive_branch_cannot_be_approved(self):
        self.tehran.is_active = False
        self.tehran.save(
            update_fields=["is_active"],
        )

        membership = self.create_pending_membership(
            self.tehran,
        )

        self.authenticate(self.manager)

        response = self.client.post(
            self.get_url(membership),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        membership.refresh_from_db()

        self.assertEqual(
            membership.status,
            CustomerBranchMembership.Status.PENDING,
        )

    def test_nonexistent_membership_returns_not_found(self):
        self.authenticate(self.manager)

        response = self.client.post(
            reverse(
                "freight:freight-api-v1:customer-branch-membership-approve",
                kwargs={
                    "membership_id": 999999,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["code"],
            "NOT_FOUND",
        )

class CurrentCustomerActiveMembershipsAPITests(FreightAPITestCase):
    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Center",
            code="THR",
        )
        self.other_branch = self.create_branch(
            name="Karaj Center",
            code="KRJ",
            city="Karaj",
        )

        self.customer_user = self.create_user(
            mobile="09121112221",
        )
        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.other_customer_user = self.create_user(
            mobile="09121112222",
        )
        self.other_customer = self.create_customer(
            user=self.other_customer_user,
        )

        self.url = reverse(
            "freight:freight-api-v1:"
            "customer-active-branch-memberships"
        )

    def create_membership(self, customer, branch, membership_status):
        return CustomerBranchMembership.objects.create(
            customer=customer,
            branch=branch,
            status=membership_status,
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_returns_only_own_active_memberships(self):
        self.create_membership(
            self.customer,
            self.branch,
            CustomerBranchMembership.Status.ACTIVE,
        )
        self.create_membership(
            self.customer,
            self.other_branch,
            CustomerBranchMembership.Status.ACTIVE,
        )

        # This membership must never appear in the current customer's list.
        self.create_membership(
            self.other_customer,
            self.branch,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        results = response.data["results"]

        self.assertEqual(len(results), 2)
        self.assertEqual(
            {item["branch"]["id"] for item in results},
            {self.branch.id, self.other_branch.id},
        )
        self.assertTrue(
            all(item["status"] == "active" for item in results)
        )
    def test_excludes_non_active_memberships(self):
        self.create_membership(
            self.customer,
            self.branch,
            CustomerBranchMembership.Status.PENDING,
        )
        self.create_membership(
            self.customer,
            self.other_branch,
            CustomerBranchMembership.Status.SUSPENDED,
        )

        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_excludes_memberships_for_inactive_branches(self):
        inactive_branch = self.create_branch(
            name="Inactive Branch",
            code="INA",
            is_active=False,
        )
        self.create_membership(
            self.customer,
            inactive_branch,
            CustomerBranchMembership.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_user_without_customer_profile_gets_empty_list(self):
        user_without_customer = self.create_user(
            mobile="09121112223",
        )

        self.client.force_authenticate(user=user_without_customer)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])