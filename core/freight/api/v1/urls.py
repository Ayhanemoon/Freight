from django.urls import include, path
from rest_framework.routers import DefaultRouter

from freight.api.v1.views import (
    BranchViewSet,
    CustomerViewSet,
    FreightCompanyViewSet,
    ShipmentOrderViewSet
)

app_name = "freight-api-v1"

router = DefaultRouter()

router.register(
    r"branches",
    BranchViewSet,
    basename="branch",
)

router.register(
    r"customers",
    CustomerViewSet,
    basename="customer",
)

router.register(
    r"freight-companies",
    FreightCompanyViewSet,
    basename="freight-company",
)

router.register(
    r"shipment-orders",
    ShipmentOrderViewSet,
    basename="shipment-order",
)

urlpatterns = [
    path("", include(router.urls)),
]