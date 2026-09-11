from rest_framework.viewsets import ModelViewSet

from freight.api.v1.serializers import ParcelSerializer
from freight.models import Parcel


class ParcelViewSet(ModelViewSet):
    serializer_class = ParcelSerializer

    queryset = (
        Parcel.objects
        .select_related(
            "order",
            "order__branch",
            "order__customer",
            "verified_by",
        )
        .all()
    )