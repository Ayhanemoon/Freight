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

    DispatchBatchViewSet,
    DispatchOrderViewSet,
    DispatchFreightAssignmentViewSet,
    DispatchBatchCreateAPIView,
    DispatchAddOrderAPIView,
    DispatchRemoveOrderAPIView,
    DispatchAssignFreightAPIView,
    DispatchMakeReadyAPIView,
    DispatchAssignDispatcherAPIView,
    DispatchStartAPIView,
    DispatchDeliveredAPIView,
    DispatchApproveAPIView,
    DispatchRejectAPIView,
    DispatchReturnAPIView,
    DispatchCompleteAPIView,
    DispatchCancelBatchAPIView,
    DispatchCancelOrderAPIView,
    DispatchCancelAssignmentAPIView,
)

app_name = "freight-api-v1"

router = DefaultRouter()

# Register viewsets with the router

# Register viewsets for branches
router.register(
    r"branches",
    BranchViewSet,
    basename="branch",
)

# Register viewsets for customers
router.register(
    r"customers",
    CustomerViewSet,
    basename="customer",
)

# Register viewsets for freight companies
router.register(
    r"freight-companies",
    FreightCompanyViewSet,
    basename="freight-company",
)

# Register viewsets for shipment orders
router.register(
    r"shipment-orders",
    ShipmentOrderViewSet,
    basename="shipment-order",
)

# Register viewsets for parcels
router.register(
    r"parcels",
    ParcelViewSet,
    basename="parcel",
)

# Register viewsets for invoices and invoice charges
router.register(
    r"invoices",
    InvoiceViewSet,
    basename="invoice",
)

# Register viewsets for collection tasks
router.register(
    r"collection-tasks",
    CollectionTaskViewSet,
    basename="collection-task",
)

# Register viewsets for dispatch batches, orders, and assignments
router.register(
    r"dispatch-batches",
    DispatchBatchViewSet,
    basename="dispatch-batch",
)

router.register(
    r"dispatch-orders",
    DispatchOrderViewSet,
    basename="dispatch-order",
)

router.register(
    r"dispatch-assignments",
    DispatchFreightAssignmentViewSet,
    basename="dispatch-assignment",
)

# Define additional URL patterns for non-viewset views
urlpatterns = [
    path("", include(router.urls)),
    # Additional URL patterns for invoice charges
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
    # Additional URL patterns for collection task actions
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

    # Additional URL patterns for dispatch actions
        path(
        "dispatch-batches/create/",
        DispatchBatchCreateAPIView.as_view(),
        name="dispatch-batch-create",
    ),

    path(
        "dispatch-batches/<int:batch_id>/add-order/",
        DispatchAddOrderAPIView.as_view(),
        name="dispatch-add-order",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/remove/",
        DispatchRemoveOrderAPIView.as_view(),
        name="dispatch-remove-order",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/assign-freight/",
        DispatchAssignFreightAPIView.as_view(),
        name="dispatch-assign-freight",
    ),

    path(
        "dispatch-batches/<int:batch_id>/ready/",
        DispatchMakeReadyAPIView.as_view(),
        name="dispatch-batch-ready",
    ),

    path(
        "dispatch-batches/<int:batch_id>/assign-dispatcher/",
        DispatchAssignDispatcherAPIView.as_view(),
        name="dispatch-assign-dispatcher",
    ),

    path(
        "dispatch-batches/<int:batch_id>/start/",
        DispatchStartAPIView.as_view(),
        name="dispatch-batch-start",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/delivered/",
        DispatchDeliveredAPIView.as_view(),
        name="dispatch-order-delivered",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/approve/",
        DispatchApproveAPIView.as_view(),
        name="dispatch-order-approve",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/reject/",
        DispatchRejectAPIView.as_view(),
        name="dispatch-order-reject",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/return/",
        DispatchReturnAPIView.as_view(),
        name="dispatch-order-return",
    ),

    path(
        "dispatch-batches/<int:batch_id>/complete/",
        DispatchCompleteAPIView.as_view(),
        name="dispatch-batch-complete",
    ),

    path(
        "dispatch-batches/<int:batch_id>/cancel/",
        DispatchCancelBatchAPIView.as_view(),
        name="dispatch-batch-cancel",
    ),

    path(
        "dispatch-orders/<int:dispatch_order_id>/cancel/",
        DispatchCancelOrderAPIView.as_view(),
        name="dispatch-order-cancel",
    ),

    path(
        "dispatch-assignments/<int:assignment_id>/cancel/",
        DispatchCancelAssignmentAPIView.as_view(),
        name="dispatch-assignment-cancel",
    ),
]