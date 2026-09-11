from django.urls import include, path
from rest_framework.routers import DefaultRouter

from freight.api.v1.views import (
    BranchViewSet,
    CustomerViewSet,
    FreightCompanyViewSet,
    ShipmentOrderViewSet,
    ParcelViewSet,
    InvoiceViewSet,
    InvoiceChargeCreateAPIView,
    InvoiceChargeDetailAPIView,
    CollectionTaskViewSet,
    CollectionTaskAssignAPIView,
    CollectionTaskVerifyParcelAPIView,
    CollectionTaskCompleteAPIView,
    CollectionTaskCancelAPIView,
    CollectionTaskFailAPIView,
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

router.register(
    r"parcels",
    ParcelViewSet,
    basename="parcel",
)

router.register(
    r"invoices",
    InvoiceViewSet,
    basename="invoice",
)

router.register(
    r"collection-tasks",
    CollectionTaskViewSet,
    basename="collection-task",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "invoices/<int:invoice_id>/charges/",
        InvoiceChargeCreateAPIView.as_view(),
        name="invoice-charge-create",
    ),

    path(
        "invoices/<int:invoice_id>/charges/<int:charge_id>/",
        InvoiceChargeDetailAPIView.as_view(),
        name="invoice-charge-detail",
    ),
    path(
        "collection-tasks/<int:task_id>/assign/",
        CollectionTaskAssignAPIView.as_view(),
        name="collection-task-assign",
    ),

    path(
        "collection-tasks/<int:task_id>/verify-parcel/",
        CollectionTaskVerifyParcelAPIView.as_view(),
        name="collection-task-verify-parcel",
    ),

    path(
        "collection-tasks/<int:task_id>/complete/",
        CollectionTaskCompleteAPIView.as_view(),
        name="collection-task-complete",
    ),

    path(
        "collection-tasks/<int:task_id>/cancel/",
        CollectionTaskCancelAPIView.as_view(),
        name="collection-task-cancel",
    ),

    path(
        "collection-tasks/<int:task_id>/fail/",
        CollectionTaskFailAPIView.as_view(),
        name="collection-task-fail",
    ),
]