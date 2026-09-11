from django.urls import include, path
from rest_framework.routers import DefaultRouter

from freight.api.v1.views import (
    BranchViewSet,
    CustomerViewSet,
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


urlpatterns = [
    path("", include(router.urls)),
]