from freight.constants.roles import Roles


def is_authenticated(user):
    return bool(user and user.is_authenticated)


def is_super_admin(user):
    return is_authenticated(user) and user.is_superuser


def has_permission(user, permission):
    """
    Check a Django permission.

    Superusers automatically pass permission checks.
    Branch scope and object ownership are handled separately.
    """
    if not is_authenticated(user):
        return False

    if user.is_superuser:
        return True

    return user.has_perm(permission)


def has_any_permission(user, *permissions):
    """
    Return True when the user has at least one of the supplied
    Django permissions.
    """
    if not is_authenticated(user):
        return False

    if user.is_superuser:
        return True

    return any(user.has_perm(permission) for permission in permissions)


def has_branch_admin_capability(user):
    """
    BranchManager has administrative capability within their own branch.

    Branch isolation must still be enforced by queryset/object/service
    checks. This function only answers whether the user has the
    administrative capability.
    """
    if not is_authenticated(user):
        return False

    return (
        user.is_superuser
        or user.groups.filter(name=Roles.BRANCH_MANAGER).exists()
    )


def has_collection_capability(user):
    """
    Collection management capability.

    This covers the existing CollectionTask permissions.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.add_collectiontask",
        "freight.assign_collection_task",
        "freight.start_collection_task",
        "freight.verify_collection_task",
        "freight.complete_collection_task",
        "freight.cancel_collection_task",
    )


def has_dispatch_management_capability(user):
    """
    Dispatch preparation/management capability.

    This is intentionally separate from dispatch execution.

    A Dispatcher should not automatically receive these permissions
    simply because they belong to the Dispatcher role.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.add_dispatchbatch",
        "freight.add_order_to_dispatch",
        "freight.remove_order_from_dispatch",
        "freight.assign_dispatcher",
        "freight.change_dispatchbatch",
    )


def has_dispatch_execution_capability(user):
    """
    Dispatch execution capability.

    Assignment/object ownership must still be checked separately.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.start_dispatch",
        "freight.complete_dispatch",
    )


def has_invoice_management_capability(user):
    """
    Invoice and invoice-charge management capability.

    This will be used by Dispatch Operators and branch administrators.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.add_invoice",
        "freight.change_invoice",
        "freight.add_invoicecharge",
        "freight.change_invoicecharge",
    )


def has_customer_management_capability(user):
    """
    Customer management capability.

    Customer ownership/access is separate from this capability.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.view_customer",
        "freight.add_customer",
        "freight.change_customer",
    )


def has_freight_company_management_capability(user):
    """
    Freight-company management capability.
    """
    if has_branch_admin_capability(user):
        return True

    return has_any_permission(
        user,
        "freight.view_freightcompany",
        "freight.add_freightcompany",
        "freight.change_freightcompany",
    )


def is_customer_user(user):
    if not is_authenticated(user):
        return False

    return (
        user.is_superuser
        or user.groups.filter(name=Roles.CUSTOMER).exists()
    )


def is_dispatcher_user(user):
    if not is_authenticated(user):
        return False

    return (
        user.is_superuser
        or user.groups.filter(name=Roles.DISPATCHER).exists()
    )


def is_cargo_collector_user(user):
    if not is_authenticated(user):
        return False

    return (
        user.is_superuser
        or user.groups.filter(name=Roles.CARGO_COLLECTOR).exists()
    )


def is_operator_user(user):
    if not is_authenticated(user):
        return False

    return (
        user.is_superuser
        or user.groups.filter(name=Roles.OPERATOR).exists()
    )