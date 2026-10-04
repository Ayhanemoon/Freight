from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from freight.api.v1.serializers import (
    CustomerBranchMembershipRequestSerializer,
    CustomerBranchMembershipSerializer,
)
from freight.services.customer_branch_membership import (
    request_customer_branch_membership,
)


class CustomerBranchMembershipRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CustomerBranchMembershipRequestSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        membership = request_customer_branch_membership(
            user=request.user,
            branch=serializer.validated_data["branch"],
        )

        response_serializer = CustomerBranchMembershipSerializer(
            membership,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )