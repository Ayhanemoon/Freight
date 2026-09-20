import pytest

from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Profile, User
from freight.models import Branch


@pytest.mark.django_db
class TestAccountsAPI:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.client = APIClient()

        self.user = User.objects.create_user(
            mobile="09121234567",
            password="test@1234567",
            is_mobile_verified=True,
            is_active=True,
        )

        self.profile = Profile.objects.get(user=self.user)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def test_user_registration(self):
        url = reverse("accounts:api-v1:register")

        data = {
            "mobile": "09121234568",
            "password": "test@1234567",
            "password1": "test@1234567",
        }

        response = self.client.post(url, data)

        print("STATUS:", response.status_code)
        print("DATA:", response.data)

        assert response.status_code == 201
        assert response.data["mobile"] == "+989121234568"
        assert response.data["detail"] == "User created successfully"

        user = User.objects.get(mobile="+989121234568")

        assert user.is_active is True
        assert user.is_mobile_verified is False

        # Profile is created automatically by the signal.
        assert Profile.objects.filter(user=user).exists()

    def test_user_registration_password_mismatch(self):
        url = reverse("accounts:api-v1:register")

        data = {
            "mobile": "09121234569",
            "password": "test@1234567",
            "password1": "different@123",
        }

        response = self.client.post(url, data)

        assert response.status_code == 400
        assert "details" in response.data

    def test_user_registration_invalid_mobile(self):
        url = reverse("accounts:api-v1:register")

        data = {
            "mobile": "123",
            "password": "test@1234567",
            "password1": "test@1234567",
        }

        response = self.client.post(url, data)

        assert response.status_code == 400
        assert "mobile" in response.data

    # ------------------------------------------------------------------
    # JWT authentication
    # ------------------------------------------------------------------

    def test_jwt_token_creation_with_local_mobile(self):
        url = reverse("accounts:api-v1:jwt_obtain_pair")

        data = {
            "mobile": "09121234567",
            "password": "test@1234567",
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_jwt_token_creation(self):
        url = reverse("accounts:api-v1:jwt_obtain_pair")

        data = {
            "mobile": "+989121234567",
            "password": "test@1234567",
        }

        response = self.client.post(url, data)

        assert response.status_code == 200

        assert "access" in response.data
        assert "refresh" in response.data
        assert "access_expires_at" in response.data
        assert "refresh_expires_at" in response.data
        assert "user_id" in response.data
        assert "mobile" in response.data

        assert response.data["mobile"] == "+989121234567"
        assert str(response.data["user_id"]) == str(self.user.id)

    def test_jwt_token_creation_requires_verified_mobile(self):
        self.user.is_mobile_verified = False
        self.user.save(update_fields=["is_mobile_verified"])

        url = reverse("accounts:api-v1:jwt_obtain_pair")

        data = {
            "mobile": "09121234567",
            "password": "test@1234567",
        }

        response = self.client.post(url, data)

        print("STATUS:", response.status_code)
        print("DATA:", response.data)

        assert response.status_code == 401

    def test_jwt_token_creation_requires_correct_password(self):
        url = reverse("accounts:api-v1:jwt_obtain_pair")

        data = {
            "mobile": "09121234567",
            "password": "wrong-password",
        }

        response = self.client.post(url, data)

        assert response.status_code == 401

    def test_jwt_token_creation_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        url = reverse("accounts:api-v1:jwt_obtain_pair")

        data = {
            "mobile": "09121234567",
            "password": "test@1234567",
        }

        response = self.client.post(url, data)

        assert response.status_code == 401

    def test_jwt_token_refresh(self):
        obtain_url = reverse("accounts:api-v1:jwt_obtain_pair")

        obtain_response = self.client.post(
            obtain_url,
            {
                "mobile": "09121234567",
                "password": "test@1234567",
            },
        )

        assert obtain_response.status_code == 200

        refresh_url = reverse("accounts:api-v1:jwt_refresh")

        response = self.client.post(
            refresh_url,
            {
                "refresh": obtain_response.data["refresh"],
            },
        )

        assert response.status_code == 200
        assert "access" in response.data

    def test_jwt_token_verify(self):
        obtain_url = reverse("accounts:api-v1:jwt_obtain_pair")

        obtain_response = self.client.post(
            obtain_url,
            {
                "mobile": "09121234567",
                "password": "test@1234567",
            },
        )

        assert obtain_response.status_code == 200

        verify_url = reverse("accounts:api-v1:jwt_verify")

        response = self.client.post(
            verify_url,
            {
                "token": obtain_response.data["access"],
            },
        )

        assert response.status_code == 200

    # ------------------------------------------------------------------
    # DRF token authentication
    # ------------------------------------------------------------------

    def test_token_login(self):
        url = reverse("accounts:api-v1:token_obtain")

        response = self.client.post(
            url,
            {
                "mobile": "09121234567",
                "password": "test@1234567",
            },
        )

        assert response.status_code == 200
        assert "token" in response.data
        assert "user_id" in response.data
        assert "mobile" in response.data

        assert response.data["mobile"] == "+989121234567"

    def test_token_login_requires_verified_mobile(self):
        self.user.is_mobile_verified = False
        self.user.save(update_fields=["is_mobile_verified"])

        url = reverse("accounts:api-v1:token_obtain")

        response = self.client.post(
            url,
            {
                "mobile": "09121234567",
                "password": "test@1234567",
            },
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    def test_profile_created_automatically(self):
        assert Profile.objects.filter(user=self.user).exists()

        profile = Profile.objects.get(user=self.user)

        assert profile.user == self.user

    def test_get_profile_requires_authentication(self):
        url = reverse("accounts:api-v1:profile")

        response = self.client.get(url)

        assert response.status_code == 401

    def test_get_profile(self):
        self.authenticate()

        url = reverse("accounts:api-v1:profile")

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["mobile"] == "+989121234567"

    def test_update_profile(self):
        self.authenticate()

        url = reverse("accounts:api-v1:profile")

        response = self.client.patch(
            url,
            {
                "first_name": "Ayhan",
                "last_name": "Samimi",
                "description": "Freight system user",
            },
        )

        assert response.status_code == 200

        self.profile.refresh_from_db()

        assert self.profile.first_name == "Ayhan"
        assert self.profile.last_name == "Samimi"
        assert self.profile.description == "Freight system user"

    # ------------------------------------------------------------------
    # Change password
    # ------------------------------------------------------------------

    def test_change_password(self):
        self.authenticate()

        url = reverse("accounts:api-v1:change-password")

        response = self.client.put(
            url,
            {
                "old_password": "test@1234567",
                "new_password": "newtest@1234567",
                "new_password1": "newtest@1234567",
            },
        )

        assert response.status_code == 200

        self.user.refresh_from_db()

        assert self.user.check_password("newtest@1234567")

    def test_change_password_requires_authentication(self):
        url = reverse("accounts:api-v1:change-password")

        response = self.client.put(
            url,
            {
                "old_password": "test@1234567",
                "new_password": "newtest@1234567",
                "new_password1": "newtest@1234567",
            },
        )

        assert response.status_code == 401

    def test_change_password_rejects_wrong_old_password(self):
        self.authenticate()

        url = reverse("accounts:api-v1:change-password")

        response = self.client.put(
            url,
            {
                "old_password": "wrong-password",
                "new_password": "newtest@1234567",
                "new_password1": "newtest@1234567",
            },
        )

        assert response.status_code == 400
        assert "old_password" in response.data

    def test_change_password_rejects_password_mismatch(self):
        self.authenticate()

        url = reverse("accounts:api-v1:change-password")

        response = self.client.put(
            url,
            {
                "old_password": "test@1234567",
                "new_password": "newtest@1234567",
                "new_password1": "different@1234567",
            },
        )

        assert response.status_code == 400

    # ------------------------------------------------------------------
    # Password reset
    # ------------------------------------------------------------------

    def test_password_reset_request(self):
        url = reverse("accounts:api-v1:reset-password-request")

        response = self.client.post(
            url,
            {
                "mobile": "09121234567",
            },
        )

        assert response.status_code == 200
        assert response.data["success"] == (
            "We have sent you a link to reset your password"
        )

    def test_password_reset_request_unknown_mobile(self):
        url = reverse("accounts:api-v1:reset-password-request")

        response = self.client.post(
            url,
            {
                "mobile": "09129999999",
            },
        )

        assert response.status_code == 400

    # ------------------------------------------------------------------
    # User list
    # ------------------------------------------------------------------

    def test_user_list_requires_authentication(self):
        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(url)

        assert response.status_code == 401

    def test_superuser_can_list_all_users(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save(update_fields=["is_superuser", "is_staff"])

        self.client.force_authenticate(user=self.user)

        User.objects.create_user(
            mobile="09121234568",
            password="test@1234567",
            is_mobile_verified=True,
        )

        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_authorized_branch_user_can_list_users_from_same_branch(self):
        branch = Branch.objects.create(
            name="Tehran Branch",
            code="THR",
            city="Tehran",
        )

        self.user.branch = branch
        self.user.save(update_fields=["branch"])

        permission = Permission.objects.get(
            codename="view_user",
            content_type__app_label="accounts",
        )

        group = Group.objects.create(name="User Viewer")
        group.permissions.add(permission)
        self.user.groups.add(group)

        same_branch_user = User.objects.create_user(
            mobile="09121234568",
            password="test@1234567",
            is_mobile_verified=True,
            branch=branch,
        )

        other_branch = Branch.objects.create(
            name="Mashhad Branch",
            code="MHD",
            city="Mashhad",
        )

        User.objects.create_user(
            mobile="09121234569",
            password="test@1234567",
            is_mobile_verified=True,
            branch=other_branch,
        )

        self.client.force_authenticate(user=self.user)

        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(url)

        assert response.status_code == 200

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        assert self.user.id in returned_ids
        assert same_branch_user.id in returned_ids

        # User from another branch must not be returned.
        assert response.data["count"] == 2

    def test_user_without_view_permission_cannot_list_users(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(url)

        assert response.status_code == 403

    def test_invalid_page_returns_invalid_page_error_code(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(
            url,
            {"page": 999999},
        )

        assert response.status_code == 404
        assert response.data["code"] == "INVALID_PAGE"
        assert response.data["detail"] == "Invalid page."

    def test_normal_not_found_still_returns_not_found_error_code(self):
        self.client.force_authenticate(user=self.user)

        url = reverse("accounts:api-v1:user-list")

        response = self.client.get(
            url,
            {"page": 999999},
        )

        assert response.status_code == 404