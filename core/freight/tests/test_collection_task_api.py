from django.urls import reverse
from django.contrib.auth.models import Group

from freight.constants import Roles
from freight.models import CollectionTask

from .base import FreightAPITestCase


class CollectionTaskListAPITests(FreightAPITestCase):
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

        self.superuser = self.create_user(
            mobile="09121111111",
            is_staff=True,
            is_superuser=True,
        )

        self.branch_manager = self.create_user(
            mobile="09121111112",
            branch=self.branch,
            is_staff=True,
        )
        self.branch_manager.groups.create(
            name=Roles.BRANCH_MANAGER,
        )

        self.customer_user = self.create_user(
            mobile="09121111113",
        )
        self.customer = self.create_customer(
            user=self.customer_user,
        )

        self.branch_order = self.create_order(
            branch=self.branch,
            customer=self.customer,
            created_by=self.customer_user,
        )
        self.other_branch_order = self.create_order(
            branch=self.other_branch,
            customer=self.customer,
            created_by=self.customer_user,
        )

        self.branch_task = CollectionTask.objects.create(
            order=self.branch_order,
            task_type=CollectionTask.Type.CUSTOMER_DELIVERY,
        )
        self.other_branch_task = CollectionTask.objects.create(
            order=self.other_branch_order,
            task_type=CollectionTask.Type.COLLECTOR_PICKUP,
        )

        self.url = reverse(
            "freight:freight-api-v1:collection-task-list"
        )

    def test_superuser_can_filter_tasks_by_branch(self):
        self.authenticate(self.superuser)

        response = self.client.get(
            self.url,
            {"branch": self.other_branch.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {self.other_branch_task.id},
        )

    def test_superuser_sees_all_tasks_without_branch_filter(self):
        self.authenticate(self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {self.branch_task.id, self.other_branch_task.id},
        )

    def test_branch_manager_cannot_filter_into_another_branch(self):
        self.authenticate(self.branch_manager)

        response = self.client.get(
            self.url,
            {"branch": self.other_branch.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_invalid_branch_filter_returns_validation_error(self):
        self.authenticate(self.superuser)

        response = self.client.get(
            self.url,
            {"branch": "not-a-number"},
        )

        self.assertEqual(response.status_code, 400)