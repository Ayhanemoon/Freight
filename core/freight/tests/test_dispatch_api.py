from django.urls import reverse
from rest_framework import status

from freight.models import DispatchBatch, DispatchOrder, ShipmentOrder

from .base import FreightAPITestCase


class DispatchBatchAPITests(FreightAPITestCase):
    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
        )

        self.operator = self.create_user(
            mobile="09120000001",
            branch=self.branch,
            is_staff=True,
        )

        self.other_branch_user = self.create_user(
            mobile="09120000002",
            branch=self.other_branch,
            is_staff=True,
        )

        self.authenticate(self.operator)

        self.list_url = reverse(
            "freight:freight-api-v1:dispatch-batch-list"
        )

        self.create_url = reverse(
            "freight:freight-api-v1:dispatch-batch-create"
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_list_dispatch_batches(self):
        self.unauthenticate()

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unauthenticated_user_cannot_create_dispatch_batch(self):
        self.unauthenticate()

        response = self.client.post(
            self.create_url,
            {
                "branch": self.branch.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_operator_can_create_dispatch_batch(self):
        self.grant_permission(
            self.operator,
            "add_dispatchbatch",
        )

        response = self.client.post(
            self.create_url,
            {
                "branch": self.branch.id,
                "notes": "Test dispatch batch",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            DispatchBatch.objects.count(),
            1,
        )

        batch = DispatchBatch.objects.get()

        self.assertEqual(
            batch.branch_id,
            self.branch.id,
        )

        self.assertEqual(
            batch.created_by_id,
            self.operator.id,
        )

        self.assertEqual(
            batch.status,
            DispatchBatch.Status.DRAFT,
        )

    def test_user_cannot_create_batch_for_another_branch(self):
        self.grant_permission(
            self.operator,
            "add_dispatchbatch",
        )

        response = self.client.post(
            self.create_url,
            {
                "branch": self.other_branch.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            DispatchBatch.objects.count(),
            0,
        )

    def test_user_without_create_permission_cannot_create_batch(self):
        response = self.client.post(
            self.create_url,
            {
                "branch": self.branch.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ------------------------------------------------------------------
    # List / branch isolation
    # ------------------------------------------------------------------

    def test_user_only_sees_dispatch_batches_from_own_branch(self):
        own_batch = DispatchBatch.objects.create(
            branch=self.branch,
            created_by=self.operator,
        )

        DispatchBatch.objects.create(
            branch=self.other_branch,
            created_by=self.other_branch_user,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        self.assertIn(
            own_batch.id,
            returned_ids,
        )

        self.assertEqual(
            len(returned_ids),
            1,
        )

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_user_can_retrieve_own_branch_batch(self):
        batch = DispatchBatch.objects.create(
            branch=self.branch,
            created_by=self.operator,
        )

        url = reverse(
            "freight:freight-api-v1:dispatch-batch-detail",
            kwargs={"pk": batch.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            batch.id,
        )

    def test_user_cannot_retrieve_other_branch_batch(self):
        batch = DispatchBatch.objects.create(
            branch=self.other_branch,
            created_by=self.other_branch_user,
        )

        url = reverse(
            "freight:freight-api-v1:dispatch-batch-detail",
            kwargs={"pk": batch.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class DispatchOrderAPITests(FreightAPITestCase):
    def setUp(self):
        self.branch = self.create_branch(
            name="Tehran Branch",
            code="THR",
        )

        self.other_branch = self.create_branch(
            name="Mashhad Branch",
            code="MHD",
        )

        self.operator = self.create_user(
            mobile="09120000101",
            branch=self.branch,
            is_staff=True,
        )

        self.other_branch_user = self.create_user(
            mobile="09120000102",
            branch=self.other_branch,
            is_staff=True,
        )

        self.customer = self.create_customer(
            user=self.create_user(
                mobile="09120000103",
                email="customer3@example.com",
            )
        )

        self.other_customer = self.create_customer(
            user=self.create_user(
                mobile="09120000104",
                email="customer4@example.com",
            )
        )

        self.authenticate(self.operator)

        self.batch = DispatchBatch.objects.create(
            branch=self.branch,
            created_by=self.operator,
        )

        self.order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.operator,
            status=ShipmentOrder.Status.READY_FOR_DISPATCH,
        )

        self.add_order_url = reverse(
            "freight:freight-api-v1:dispatch-add-order",
            kwargs={"batch_id": self.batch.pk},
        )

    # ------------------------------------------------------------------
    # Add order
    # ------------------------------------------------------------------

    def test_can_add_ready_order_to_draft_batch(self):
        self.grant_permission(
            self.operator,
            "add_order_to_dispatch",
        )

        response = self.client.post(
            self.add_order_url,
            {
                "order": self.order.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        dispatch_order = DispatchOrder.objects.get()

        self.assertEqual(
            dispatch_order.batch_id,
            self.batch.id,
        )

        self.assertEqual(
            dispatch_order.order_id,
            self.order.id,
        )

        self.assertEqual(
            dispatch_order.status,
            DispatchOrder.Status.PENDING,
        )

    def test_cannot_add_order_from_another_branch(self):
        self.grant_permission(
            self.operator,
            "add_order_to_dispatch",
        )

        other_order = self.create_order(
            branch=self.other_branch,
            customer=self.other_customer,
            created_by=self.other_branch_user,
            status=ShipmentOrder.Status.READY_FOR_DISPATCH,
        )

        response = self.client.post(
            self.add_order_url,
            {
                "order": other_order.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            DispatchOrder.objects.count(),
            0,
        )

    def test_cannot_add_order_that_is_not_ready_for_dispatch(self):
        self.grant_permission(
            self.operator,
            "add_order_to_dispatch",
        )

        self.order.status = (
            ShipmentOrder.Status.INVOICE_REGISTERED
        )
        self.order.save(
            update_fields=["status"]
        )

        response = self.client.post(
            self.add_order_url,
            {
                "order": self.order.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            DispatchOrder.objects.count(),
            0,
        )

    def test_cannot_add_same_order_twice(self):
        self.grant_permission(
            self.operator,
            "add_order_to_dispatch",
        )

        first_response = self.client.post(
            self.add_order_url,
            {
                "order": self.order.id,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.add_order_url,
            {
                "order": self.order.id,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            DispatchOrder.objects.count(),
            1,
        )

    # ------------------------------------------------------------------
    # Remove order
    # ------------------------------------------------------------------

    def test_can_remove_order_from_draft_batch(self):
        self.grant_permission(
            self.operator,
            "remove_order_from_dispatch",
        )

        dispatch_order = DispatchOrder.objects.create(
            batch=self.batch,
            order=self.order,
        )

        url = reverse(
            "freight:freight-api-v1:dispatch-remove-order",
            kwargs={
                "dispatch_order_id": dispatch_order.pk,
            },
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            DispatchOrder.objects.filter(
                pk=dispatch_order.pk,
            ).exists()
        )

    def test_cannot_remove_order_without_permission(self):
        dispatch_order = DispatchOrder.objects.create(
            batch=self.batch,
            order=self.order,
        )

        url = reverse(
            "freight:freight-api-v1:dispatch-remove-order",
            kwargs={
                "dispatch_order_id": dispatch_order.pk,
            },
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            DispatchOrder.objects.filter(
                pk=dispatch_order.pk,
            ).exists()
        )