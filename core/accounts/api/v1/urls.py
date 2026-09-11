from django.urls import path
from .views import (
    RegisterApiView,
    VerifyEmailApiView,
    ResendVerifyEmailApiView,
    ChangePasswordView,
    PasswordResetRequestEmailApiView,
    PasswordResetTokenValidateApiView,
    PasswordResetSetNewApiView,
    ObtainTokenApiView,
    DiscardAuthTokenApiView,
    JWTObtainPairTokenApiView,
    ProfileApiView,
    UserListApiView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "api-v1"

urlpatterns = [
    # Registration management
    path("register/", RegisterApiView.as_view(), name="register"),
    path(
        "register/email-verify/",
        VerifyEmailApiView.as_view(),
        name="email_verify",
    ),
    path(
        "register/email-verify/resend/",
        ResendVerifyEmailApiView.as_view(),
        name="email_verify_resend",
    ),
    # Password management
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "reset-password/",
        PasswordResetRequestEmailApiView.as_view(),
        name="reset-password-request",
    ),
    path(
        "reset-password/validate-token/",
        PasswordResetTokenValidateApiView.as_view(),
        name="reset-password-validate",
    ),
    path(
        "reset-password/set-password/",
        PasswordResetSetNewApiView.as_view(),
        name="reset-password-confirm",
    ),
    # Token authentication mechanism
    path("token/login/", ObtainTokenApiView.as_view(), name="token_obtain"),
    path(
        "token/logout/",
        DiscardAuthTokenApiView.as_view(),
        name="token_discard",
    ),
    # JWT authentication mechanism
    path("jwt/create/", JWTObtainPairTokenApiView.as_view(), name="jwt_obtain_pair"),
    path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
    path("jwt/verify/", TokenVerifyView.as_view(), name="jwt_verify"),
    # User profile management
    path("profile/", ProfileApiView.as_view(), name="profile"),
    path(
        "users/",
        UserListApiView.as_view(),
        name="user-list",
    ),
]
