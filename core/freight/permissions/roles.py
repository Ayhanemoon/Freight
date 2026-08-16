from freight.constants.roles import Roles


def user_has_role(user, role):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=role).exists()


def is_cargo_collector(user):
    return user_has_role(user, Roles.CARGO_COLLECTOR)


def is_operator(user):
    return user_has_role(user, Roles.OPERATOR)


def is_branch_manager(user):
    return user_has_role(user, Roles.BRANCH_MANAGER)


def is_dispatcher(user):
    return user_has_role(user, Roles.DISPATCHER)


def is_customer(user):
    return user_has_role(user, Roles.CUSTOMER)