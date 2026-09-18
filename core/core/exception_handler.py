from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.api_errors import ErrorCode


DRF_ERROR_CODE_MAP = {
    "not_authenticated": ErrorCode.AUTHENTICATION_REQUIRED,
    "authentication_failed": ErrorCode.AUTHENTICATION_FAILED,
    "permission_denied": ErrorCode.PERMISSION_DENIED,
    "not_found": ErrorCode.NOT_FOUND,
    "method_not_allowed": ErrorCode.METHOD_NOT_ALLOWED,
    "parse_error": ErrorCode.PARSE_ERROR,
    "unsupported_media_type": ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    "not_acceptable": ErrorCode.NOT_ACCEPTABLE,
    "throttled": ErrorCode.THROTTLED,
    "invalid": ErrorCode.VALIDATION_ERROR,
}


def exception_handler(exc, context):
    """
    Global API exception handler.

    Converts Django and DRF exceptions into a consistent API response:

    {
        "code": "ERROR_CODE",
        "detail": "Human-readable detail",
        "errors": {...}  # optional
    }
    """

    # Django exceptions that may still be raised
    # by the service layer during migration.
    if isinstance(exc, DjangoPermissionDenied):
        return Response(
            {
                "code": ErrorCode.PERMISSION_DENIED,
                "detail": str(exc),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            errors = exc.message_dict
        else:
            errors = exc.messages

        return Response(
            {
                "code": ErrorCode.VALIDATION_ERROR,
                "detail": "Request validation failed.",
                "errors": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Let DRF handle its own exceptions first.
    response = drf_exception_handler(exc, context)

    # Unknown/unhandled exception.
    if response is None:
        return None

    # Authentication
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {
            "code": ErrorCode.AUTHENTICATION_REQUIRED,
            "detail": str(response.data.get("detail", "")),
        }
        return response

    # Permission
    if response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {
            "code": ErrorCode.PERMISSION_DENIED,
            "detail": str(response.data.get("detail", "")),
        }
        return response

    # Not found
    if response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {
            "code": ErrorCode.NOT_FOUND,
            "detail": str(response.data.get("detail", "")),
        }
        return response

    # Bad request / validation
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        code = getattr(exc, "default_code", None)

        if isinstance(code, str):
            code = DRF_ERROR_CODE_MAP.get(code, code.upper())
        else:
            code = ErrorCode.VALIDATION_ERROR

        if isinstance(response.data, dict) and "detail" in response.data:
            detail = str(response.data["detail"])
            errors = None
        else:
            detail = "Request validation failed."
            errors = response.data

        data = {
            "code": code,
            "detail": detail,
        }

        if errors is not None:
            data["errors"] = errors

        response.data = data
        return response

    return response