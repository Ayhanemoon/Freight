from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import ShipmentOrderSerializer
from freight.models import ShipmentOrder


class ShipmentOrderViewSet(ModelViewSet):
    serializer_class = ShipmentOrderSerializer

    queryset = (
        ShipmentOrder.objects
        .select_related(
            "branch",
            "customer",
            "customer__user",
            "preferred_freight_company",
            "created_by",
        )
        .prefetch_related(
            "parcels",
        )
        .all()
    )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)