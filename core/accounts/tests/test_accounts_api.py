from django.urls import reverse
from rest_framework.test import APIClient
import pytest

from accounts.models import User, Profile


@pytest.mark.django_db
class TestPostAPI:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test@1234567",
            is_mobile_verified=True,
            is_active=True,
        )
        self.profile = Profile.objects.get(user=self.user)
        # self.client.force_authenticate(user=self.user)

        """
        test for User Registration, email verification, jwt token createion, refresh token, verify, password reset email, password reset confirm, profile update,
        """

    def test_user_registration(self):
        url = reverse("accounts:api-v1:register")
        data = {
            "email": "test2@test.com",
            "password": "test@1234567",
            "password1": "test@1234567",
        }
        response = self.client.post(url, data)
        assert response.status_code == 201
        assert response.data["email"] == "test2@test.com"
        """check for profile creation after registration"""
        assert Profile.objects.filter(user__email="test2@test.com").exists()

    # def test_email_verification_sent(self):
    #     url = reverse('accounts:api-v1:email_verify')
    #     data = {
    #         'email': 'test@test.com',
    #     }
    #     response = self.client.post(url, data)
    #     assert response.status_code == 200
    #     assert response.data['message'] == 'Verification email sent.'

    def test_jwt_token_creation(self):
        url = reverse("accounts:api-v1:jwt_obtain_pair")
        data = {
            "email": "test@test.com",
            "password": "test@1234567",
        }
        response = self.client.post(url, data)

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_jwt_token_refresh(self):
        # First obtain a token
        obtain_url = reverse("accounts:api-v1:jwt_obtain_pair")
        data = {
            "email": "test@test.com",
            "password": "test@1234567",
        }
        obtain_response = self.client.post(obtain_url, data)
        refresh_token = obtain_response.data["refresh"]

        # Now refresh the token
        refresh_url = reverse("accounts:api-v1:jwt_refresh")
        refresh_data = {
            "refresh": refresh_token,
        }
        refresh_response = self.client.post(refresh_url, refresh_data)
        assert refresh_response.status_code == 200
        assert "access" in refresh_response.data

    def test_jwt_token_verify(self):
        # First obtain a token
        obtain_url = reverse("accounts:api-v1:jwt_obtain_pair")
        data = {
            "email": "test@test.com",
            "password": "test@1234567",
        }
        obtain_response = self.client.post(obtain_url, data)
        access_token = obtain_response.data["access"]

        # Now verify the token
        verify_url = reverse("accounts:api-v1:jwt_verify")
        verify_data = {
            "token": access_token,
        }
        verify_response = self.client.post(verify_url, verify_data)
        assert verify_response.status_code == 200

    def test_password_reset_email(self):
        url = reverse("accounts:api-v1:reset-password-request")
        data = {
            "email": "test@test.com",
        }
        response = self.client.post(url, data)
        assert response.status_code == 200
        assert (
            response.data["success"] == "We have sent you a link to reset your password"
        )
