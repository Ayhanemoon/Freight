
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from freight.api.v1.serializers import (
    ShipmentOrderActionSerializer,
    ShipmentOrderSerializer,
)
from freight.models import ShipmentOrder
from freight.permissions.capabilities import (
    has_branch_admin_capability,
    is_operator_user,
    has_permission,
)
from freight.services import receive_shipment_at_branch

class BranchReceiveShipmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user = request.user

        # Branch managers, operators, and explicitly authorized users.
        can_receive = (
            has_branch_admin_capability(user)
            or is_operator_user(user)
            or has_permission(
                user,
                "freight.receive_shipment_at_branch",
            )
        )

        if not can_receive:
            raise PermissionDenied(
                "You do not have permission to receive shipments."
            )

        queryset = ShipmentOrder.objects.select_related("branch")

        # Restrict access to the user's own branch.
        if not user.is_superuser:
            if not user.branch_id:
                raise PermissionDenied(
                    "A branch is required to receive shipments."
                )

            queryset = queryset.filter(branch_id=user.branch_id)

        order = get_object_or_404(queryset, pk=order_id)

        serializer = ShipmentOrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = receive_shipment_at_branch(
                order=order,
                received_by=user,
                note=(
                    serializer.validated_data.get("note")
                    or "Shipment received at branch."
                ),
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ShipmentOrderSerializer(
                order,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )
