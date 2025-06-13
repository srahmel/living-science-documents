from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
import logging

logger = logging.getLogger(__name__)

def format_error_response(message, status_code=status.HTTP_400_BAD_REQUEST, log_error=True, exc=None):
    """
    Utility function to format error responses consistently across the API.

    Args:
        message (str): The error message to return to the client
        status_code (int): The HTTP status code to return
        log_error (bool): Whether to log the error
        exc (Exception, optional): The exception that caused the error, for logging

    Returns:
        Response: A DRF Response object with the error message
    """
    if log_error:
        if exc:
            logger.error(f"API Error: {message} - Exception: {str(exc)}")
        else:
            logger.error(f"API Error: {message}")

    return Response({'error': message}, status=status_code)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures all API requests receive JSON responses.
    This handler extends the default DRF exception handler to handle additional exceptions
    and ensure that all responses are in JSON format, even when DEBUG=True.
    """
    # First, get the standard DRF response (if any)
    response = exception_handler(exc, context)

    # If DRF already handled it, convert the response format if needed
    if response is not None:
        # If the response has a 'detail' field, convert it to 'error'
        if 'detail' in response.data:
            error_message = response.data['detail']
            response.data = {'error': error_message}
        return response

    # Handle Django's Http404 exception
    if isinstance(exc, Http404):
        return format_error_response('Not found.', status.HTTP_404_NOT_FOUND, exc=exc)

    # Handle Django's PermissionDenied exception
    if isinstance(exc, PermissionDenied):
        return format_error_response('Permission denied.', status.HTTP_403_FORBIDDEN, exc=exc)

    # Handle database ProtectedError (when trying to delete an object that has related objects)
    if isinstance(exc, ProtectedError):
        return format_error_response(
            'Cannot delete this object because it is referenced by other objects.',
            status.HTTP_400_BAD_REQUEST,
            exc=exc
        )

    # Handle any other exceptions
    if exc:
        return format_error_response(
            str(exc),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            exc=exc
        )

    # If we get here, something unexpected happened
    return format_error_response(
        'An unexpected error occurred.',
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )
