import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler to standardize error responses.
    """
    response = exception_handler(exc, context)

    if response is None:
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}",
            exc_info=True,
            extra={
                "view": context.get("view"),
                "request": context.get("request"),
            }
        )
        return Response(
            {"error": "Internal server error. Please contact support."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Log error
    logger.warning(
        f"API Error: {response.status_code} - {exc.__class__.__name__}",
        extra={
            "status_code": response.status_code,
            "exception": exc.__class__.__name__,
            "detail": str(exc),
        }
    )

    # Standardize response
    if isinstance(response.data, dict) and "detail" in response.data:
        return Response(
            {"error": response.data["detail"]},
            status=response.status_code
        )
    elif isinstance(response.data, dict) and "non_field_errors" in response.data:
        return Response(
            {"error": response.data["non_field_errors"][0] if response.data["non_field_errors"] else "Invalid input"},
            status=response.status_code
        )

    return response
