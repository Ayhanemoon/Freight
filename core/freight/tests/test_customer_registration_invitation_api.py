from datetime import timedelta

from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from freight.constants import Roles
from freight.models import (
    Customer,
    CustomerBranchMembership,
    CustomerRegistrationInvitation,
)
from freight.services.customer_registration_invitation import (
    create_customer_registration_invitation,
)
from freight.tests.base import FreightAPITestCase


class CustomerRegistrationInvitationAPITests(
    FreightAPITestCase
):

    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        self.manager = self.create_user(
            mobile="09121111111",
            branch=self.branch,
            is_staff=True,
        )

        manager_group = Group.objects.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.manager.groups.add(
            manager_group,
        )

        self.url = reverse(
            "freight:freight-api-v1:customer-registration-invitation"
        )

    def create_invitation(
        self,
        branch=None,
        target_mobile=None,
        customer=None,
        expires_at=None,
        max_uses=1,
    ):
        return create_customer_registration_invitation(
            user=self.manager,
            branch=branch or self.branch,
            target_mobile=target_mobile,
            customer=customer,
            expires_at=expires_at,
            max_uses=max_uses,
        )

    def valid_person_payload(
        self,
        token,
        mobile="09121234567",
    ):
        return {
            "invitation_token": token,
            "mobile": mobile,
            "password": "test@123456",
            "password1": "test@123456",
            "customer_type": Customer.CustomerType.PERSON,
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "national_id": "0012345678",
        }

    def test_customer_can_register_with_generic_invitation(self):
        invitation, token = self.create_invitation()

        response = self.client.post(
            self.url,
            self.valid_person_payload(token),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertIn(
            "user",
            response.data,
        )

        self.assertIn(
            "customer",
            response.data,
        )

        self.assertIn(
            "membership",
            response.data,
        )

        self.assertEqual(
            response.data["membership"]["branch"]["id"],
            self.branch.id,
        )

        self.assertEqual(
            response.data["membership"]["status"],
            CustomerBranchMembership.Status.PENDING,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_customer_can_register_with_mobile_specific_invitation(
        self,
    ):
        mobile = "09121234568"

        invitation, token = self.create_invitation(
            target_mobile=mobile,
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile=mobile,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["user"]["mobile"],
            "+989121234568",
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )

    def test_wrong_mobile_cannot_use_mobile_specific_invitation(
        self,
    ):
        invitation, token = self.create_invitation(
            target_mobile="09121234568",
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile="09121234569",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_expired_invitation_is_rejected(self):
        invitation, token = self.create_invitation(
            expires_at=timezone.now() - timedelta(
                minutes=1,
            ),
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(token),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_revoked_invitation_is_rejected(self):
        invitation, token = self.create_invitation()

        invitation.revoked_at = timezone.now()
        invitation.save(
            update_fields=["revoked_at"],
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(token),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_customer_specific_invitation_cannot_create_new_customer(
        self,
    ):
        existing_user = self.create_user(
            mobile="09121234570",
        )

        existing_customer = self.create_customer(
            user=existing_user,
        )

        invitation, token = self.create_invitation(
            customer=existing_customer,
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile="09121234571",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_existing_mobile_cannot_register_again(self):
        existing_user = self.create_user(
            mobile="09121234572",
        )

        invitation, token = self.create_invitation()

        response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile=str(existing_user.mobile),
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_client_cannot_choose_branch(self):
        invitation, token = self.create_invitation(
            branch=self.branch,
        )

        payload = self.valid_person_payload(token)

        payload["branch"] = self.other_branch.id

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["membership"]["branch"]["id"],
            self.branch.id,
        )

        self.assertNotEqual(
            response.data["membership"]["branch"]["id"],
            self.other_branch.id,
        )

    def test_invalid_customer_data_does_not_consume_invitation(
        self,
    ):
        invitation, token = self.create_invitation()

        payload = self.valid_person_payload(token)

        payload.pop("national_id")

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            0,
        )

    def test_unauthenticated_user_can_register(self):
        invitation, token = self.create_invitation()

        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            self.url,
            self.valid_person_payload(token),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_invitation_can_only_be_used_once_by_default(self):
        invitation, token = self.create_invitation()

        first_response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile="09121234573",
            ),
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.url,
            self.valid_person_payload(
                token,
                mobile="09121234574",
            ),
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.used_count,
            1,
        )