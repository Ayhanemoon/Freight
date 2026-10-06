from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from freight.api.v1.serializers import (
    CustomerRegistrationInvitationSerializer,
    CustomerSerializer,
)
from freight.services.customer_registration_invitation import (
    register_customer_with_invitation,
)


class CustomerRegistrationInvitationAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = CustomerRegistrationInvitationSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data.copy()
        validated_data.pop("password1")

        user, customer, membership, _ = (
            register_customer_with_invitation(
                **validated_data,
            )
        )

        return Response(
            {
                "user": {
                    "id": user.id,
                    "mobile": str(user.mobile),
                },
                "customer": CustomerSerializer(
                    customer
                ).data,
                "membership": {
                    "id": membership.id,
                    "branch": {
                        "id": membership.branch_id,
                        "name": membership.branch.name,
                    },
                    "status": membership.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )