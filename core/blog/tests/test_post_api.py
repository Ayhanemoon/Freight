from django.urls import reverse
from rest_framework.test import APIClient
from django.utils import timezone
import pytest

from blog.models import Post, Category
from accounts.models import User, Profile


@pytest.mark.django_db
class TestPostAPI:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="test@1234567"
        )
        self.profile = Profile.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Test Category")
        self.post = Post.objects.create(
            author=self.profile,
            title="Test Post",
            content="This is a test post.",
            status=True,
            category=None,
            published_at=timezone.now().isoformat(),
        )

    def test_get_post_list(self):
        url = reverse("blog:api-v1:post-list")
        response = self.client.get(url)
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_get_post_detail(self):
        url = reverse("blog:api-v1:post-detail", kwargs={"pk": self.post.id})
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data["title"] == "Test Post"

    def test_create_post(self):
        url = reverse("blog:api-v1:post-list")
        data = {
            "author": self.profile.id,
            "title": "New Post",
            "content": "Content of the new post.",
            "status": True,
            "category": self.category.id,
            "published_at": timezone.now().isoformat(),
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data["title"] == "New Post"

    def test_update_post(self):
        url = reverse("blog:api-v1:post-detail", kwargs={"pk": self.post.id})
        data = {
            "title": "Updated Post",
            "content": "Updated content of the post.",
            "status": True,
            "category": self.category.id,
            "published_at": timezone.now().isoformat(),
        }
        response = self.client.put(url, data)
        assert response.status_code == 200
        assert response.data["title"] == "Updated Post"

    def test_delete_post(self):
        url = reverse("blog:api-v1:post-detail", kwargs={"pk": self.post.id})
        response = self.client.delete(url)
        assert response.status_code == 204
        assert not Post.objects.filter(id=self.post.id).exists()

    def test_post_creat_invalid_data(self):
        url = reverse("blog:api-v1:post-list")
        data = {
            "author": self.profile.id,
            "status": True,
            "category": self.category.id,
            "published_at": timezone.now().isoformat(),
        }
        response = self.client.post(url, data)
        assert response.status_code == 400
