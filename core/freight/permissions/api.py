from rest_framework.permissions import BasePermission

from freight.permissions.capabilities import (
    has_branch_admin_capability,
    has_collection_capability,
    has_customer_management_capability,
    has_dispatch_execution_capability,
    has_dispatch_management_capability,
    has_freight_company_management_capability,
    has_invoice_management_capability,
    is_cargo_collector_user,
    is_customer_user,
    is_dispatcher_user,
)


class IsBranchAdmin(BasePermission):
    """
    SuperAdmin or BranchManager.

    Branch isolation must still be enforced by the queryset/service layer.
    """

    def has_permission(self, request, view):
        return has_branch_admin_capability(request.user)


class CanManageCollection(BasePermission):
    """
    Collection management capability.

    Used for collection-operator actions such as:
    - creating collection tasks
    - assigning collectors
    - managing collection lifecycle
    """

    def has_permission(self, request, view):
        return has_collection_capability(request.user)


class CanManageDispatch(BasePermission):
    """
    Dispatch preparation/management capability.

    This is for Dispatch Operators, BranchManagers and SuperAdmins.

    It does NOT mean the user can execute an assigned dispatch.
    """

    def has_permission(self, request, view):
        return has_dispatch_management_capability(request.user)


class CanExecuteDispatch(BasePermission):
    """
    Dispatch execution capability.

    The service layer must additionally verify that the dispatcher
    is actually assigned to the relevant batch.
    """

    def has_permission(self, request, view):
        return has_dispatch_execution_capability(request.user)


class CanManageInvoices(BasePermission):
    """
    Invoice creation and charge-management capability.
    """

    def has_permission(self, request, view):
        return has_invoice_management_capability(request.user)


class CanManageCustomers(BasePermission):
    """
    Customer-management capability.
    """

    def has_permission(self, request, view):
        return has_customer_management_capability(request.user)


class CanManageFreightCompanies(BasePermission):
    """
    Freight-company management capability.
    """

    def has_permission(self, request, view):
        return has_freight_company_management_capability(request.user)


class IsCustomer(BasePermission):
    """
    Customer role.

    Ownership of shipment orders is checked separately.
    """

    def has_permission(self, request, view):
        return is_customer_user(request.user)


class IsDispatcher(BasePermission):
    """
    Dispatcher role.

    Assignment to a specific dispatch batch/order is checked separately.
    """

    def has_permission(self, request, view):
        return is_dispatcher_user(request.user)


class IsCargoCollector(BasePermission):
    """
    CargoCollector role.

    Assignment to a specific collection task is checked separately.
    """

    def has_permission(self, request, view):
        return is_cargo_collector_user(request.user)