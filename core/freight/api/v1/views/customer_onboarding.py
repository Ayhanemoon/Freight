from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from freight.api.v1.serializers import (
    CustomerOnboardingSerializer,
    CustomerSerializer,
)
from freight.services.customer_onboarding import onboard_customer


class CustomerOnboardingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CustomerOnboardingSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        customer, membership = onboard_customer(
            user=request.user,
            **serializer.validated_data,
        )

        response_data = CustomerSerializer(customer).data

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )