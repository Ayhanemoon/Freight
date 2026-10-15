from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status

from freight.constants import Roles
from freight.models import Parcel, ShipmentOrder

from .base import FreightAPITestCase


class ParcelDeletionAPITests(FreightAPITestCase):
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

        self.customer_user = self.create_user(
            mobile="09121111113",
        )
        customer_group, _ = Group.objects.get_or_create(
            name=Roles.CUSTOMER,
        )
        self.customer_user.groups.add(customer_group)
        self.customer = self.create_customer(user=self.customer_user)

        self.other_customer_user = self.create_user(
            mobile="09121111114",
        )
        self.other_customer_user.groups.add(customer_group)
        self.other_customer = self.create_customer(
            user=self.other_customer_user,
        )

        self.branch_manager = self.create_user(
            mobile="09121111115",
            branch=self.branch,
            is_staff=True,
        )
        self.branch_manager.groups.create(name=Roles.BRANCH_MANAGER)

        self.operator = self.create_user(
            mobile="09121111116",
            branch=self.branch,
            is_staff=True,
        )
        self.operator.groups.create(name=Roles.OPERATOR)

        self.cargo_collector = self.create_user(
            mobile="09121111117",
            branch=self.branch,
            is_staff=True,
        )
        self.cargo_collector.groups.create(
            name=Roles.CARGO_COLLECTOR,
        )

        self.url = reverse("freight:freight-api-v1:parcel-list")

    def create_parcel(self, order):
        return Parcel.objects.create(
            order=order,
            parcel_number=1,
            declared_weight_kg="2.00",
            declared_length_cm="20.00",
            declared_width_cm="15.00",
            declared_height_cm="10.00",
            contents_description="Test parcel",
        )

    def delete_parcel(self, user, parcel):
        self.client.force_authenticate(user=user)
        return self.client.delete(
            reverse(
                "freight:freight-api-v1:parcel-detail",
                kwargs={"pk": parcel.pk},
            )
        )

    def test_customer_can_delete_parcel_from_own_draft_order(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.customer_user, parcel)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_customer_cannot_delete_parcel_after_draft(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.SUBMITTED,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.customer_user, parcel)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_customer_cannot_delete_another_customers_parcel(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.other_customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.customer_user, parcel)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_branch_manager_can_delete_parcel_in_own_branch(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.APPROVED_FOR_COLLECTION,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.branch_manager, parcel)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_branch_manager_cannot_delete_parcel_in_another_branch(self):
        order = self.create_order(
            branch=self.other_branch,
            customer=self.customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.branch_manager, parcel)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_change_permission_alone_does_not_allow_deletion(self):
        self.grant_permission(self.operator, "change_parcel")
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.operator, parcel)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_delete_permission_allows_staff_to_delete_in_own_branch(self):
        self.grant_permission(self.operator, "delete_parcel")
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.operator, parcel)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_staff_cannot_delete_after_pre_collection_lifecycle(self):
        self.grant_permission(self.operator, "delete_parcel")
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.COLLECTED,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.operator, parcel)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())

    def test_cargo_collector_cannot_delete_through_generic_endpoint(self):
        order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            status=ShipmentOrder.Status.DRAFT,
        )
        parcel = self.create_parcel(order)

        response = self.delete_parcel(self.cargo_collector, parcel)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Parcel.objects.filter(pk=parcel.pk).exists())