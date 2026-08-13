from django.urls import reverse
from rest_framework.test import APIClient
import pytest

from blog.models import Category
from accounts.models import User, Profile


@pytest.mark.django_db
class TestCategoryAPI:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="test@1234567"
        )
        self.profile = Profile.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Test Category")

    def test_get_category_list(self):
        url = reverse("blog:api-v1:category-list")
        response = self.client.get(url)
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_get_category_detail(self):
        url = reverse("blog:api-v1:category-detail", kwargs={"pk": self.category.id})
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data["name"] == "Test Category"

    def test_create_category(self):
        url = reverse("blog:api-v1:category-list")
        data = {"name": "New Category"}
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data["name"] == "New Category"

    def test_update_category(self):
        url = reverse("blog:api-v1:category-detail", kwargs={"pk": self.category.id})
        data = {"name": "Updated Category"}
        response = self.client.put(url, data)
        assert response.status_code == 200
        assert response.data["name"] == "Updated Category"

    def test_delete_category(self):
        url = reverse("blog:api-v1:category-detail", kwargs={"pk": self.category.id})
        response = self.client.delete(url)
        assert response.status_code == 204
        assert not Category.objects.filter(pk=self.category.id).exists()
