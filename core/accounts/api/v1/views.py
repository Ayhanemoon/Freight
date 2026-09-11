from rest_framework.response import Response
from rest_framework import generics, status, views, mixins
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from accounts.models import User, Profile
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer,
    EmailVerificationSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    ObtainTokenSerializer,
    JWTObtainPairTokenSerializer,
    ResendVerifyTokenSerializer,
    PasswordResetRequestMobileSerializer,
    PasswordResetTokenVerificationSerializer,
    SetNewPasswordSerializer,
)
from ..utils import Util


class RegisterApiView(generics.GenericAPIView):

    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(mobile=serializer.validated_data["mobile"])
            return Response(
                {
                    "id": user.id,
                    "mobile": str(user.mobile),
                    "detail": "User created successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailApiView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer

    # def get(self, request):
    #     serializer = self.serializer_class(
    #         data={"token": request.query_params.get("token")}
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     user = serializer.validated_data["user"]
    #     if not user.is_mobile_verified:
    #         user.is_mobile_verified = True
    #         user.save()

    #     return Response(
    #         {"detail": "user verified successfully"},
    #         status=status.HTTP_200_OK,
    #     )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        if not user.is_mobile_verified:
            user.is_mobile_verified = True
            user.save()

        return Response(
            {"detail": "user verified successfully"}, status=status.HTTP_200_OK
        )


class ChangePasswordView(mixins.UpdateModelMixin, generics.GenericAPIView):
    """
    An endpoint for changing password.
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                "details": "Password updated successfully",
            }

            return Response(response, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileApiView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        return obj


class ObtainTokenApiView(generics.CreateAPIView):
    serializer_class = ObtainTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.mobile})


class DiscardAuthTokenApiView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        request.user.auth_token.delete()
        return Response(
            {"details": "token successfully removed"},
            status=status.HTTP_200_OK,
        )


class JWTObtainPairTokenApiView(generics.CreateAPIView):
    serializer_class = JWTObtainPairTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.pk,
                "mobile": user.mobile,
            }
        )


class ResendVerifyEmailApiView(generics.GenericAPIView):

    serializer_class = ResendVerifyTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["usrer"]
            token = RefreshToken.for_user(user).access_token
            current_site = get_current_site(request).domain
            relativeLink = reverse("accounts:api-v1:email_verify_resend")
            absurl = "http://" + current_site + relativeLink + "?token=" + str(token)
            # email_body = 'Hi '+user.email + \
            #     ' Use the link below to verify your email \n' + absurl
            # data = {'email_body': email_body, 'to_email': user.email,
            #         'email_subject': 'Verify your email'}
            # data = {'email':user.email,"link":absurl,"site":current_site}
            #  Util.send_email(data)
            data = {"email": user.email, "link": absurl, "site": current_site}
            Util.send_templated_email("email/verification_template.html", data)

            return Response(
                {"details": "verification mail has been sent"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestEmailApiView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestMobileSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = RefreshToken.for_user(user).access_token
        relativeLink = reverse("accounts:api-v1:reset-password-validate")
        current_site = get_current_site(request=request).domain
        absurl = "http://" + current_site + relativeLink + "?token=" + str(token)
        # email_body = 'Hi '+user.email + \
        #         'Use the link below to reset your password \n' + absurl
        # data = {'email_body': email_body, 'to_email': user.email,
        #             'email_subject': 'Verify your email'}

        # Util.send_email(data)
        data = {"email": user.email, "link": absurl, "site": current_site}
        Util.send_templated_email("email/reset_password_template.html", data)
        return Response(
            {"success": "We have sent you a link to reset your password"},
            status=status.HTTP_200_OK,
        )


class PasswordResetTokenValidateApiView(
    mixins.RetrieveModelMixin, generics.GenericAPIView
):
    serializer_class = PasswordResetTokenVerificationSerializer

    # def get(self, request):
    #     serializer = self.serializer_class(
    #          data={"token": request.query_params.get("token")}
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     return Response(
    #         {"detail": "Token is valid"}, status=status.HTTP_200_OK
    #     )

    def post(self, request):
        Serializer = self.serializer_class(data=request.data)
        Serializer.is_valid(raise_exception=True)

        return Response({"detail": "Token is Valid"}, status=status.HTTP_200_OK)


class PasswordResetSetNewApiView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"detail": "Password reset successfully"},
            status=status.HTTP_200_OK,
        )
