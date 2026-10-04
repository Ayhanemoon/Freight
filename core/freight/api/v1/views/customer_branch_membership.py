from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from freight.models import CustomerBranchMembership
from freight.api.v1.serializers import (
    CustomerBranchMembershipRequestSerializer,
    CustomerBranchMembershipSerializer,
)
from freight.services.customer_branch_membership import (
    approve_customer_branch_membership,
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

class CustomerBranchMembershipApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        membership_queryset = (
            CustomerBranchMembership.objects
            .select_related("branch", "customer")
        )

        if request.user.is_superuser:
            pass
        elif request.user.branch_id:
            membership_queryset = membership_queryset.filter(
                branch_id=request.user.branch_id,
            )
        else:
            membership_queryset = membership_queryset.none()

        membership = get_object_or_404(
            membership_queryset,
            id=membership_id,
        )

        membership = approve_customer_branch_membership(
            user=request.user,
            membership=membership,
        )

        response_serializer = CustomerBranchMembershipSerializer(
            membership,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )