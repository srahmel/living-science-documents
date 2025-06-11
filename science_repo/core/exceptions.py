from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError

def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures all API requests receive JSON responses.
    This handler extends the default DRF exception handler to handle additional exceptions
    and ensure that all responses are in JSON format, even when DEBUG=True.
    """
    # First, get the standard DRF response (if any)
    response = exception_handler(exc, context)

    # If DRF already handled it, return the response
    if response is not None:
        return response

    # Handle Django's Http404 exception
    if isinstance(exc, Http404):
        data = {'detail': 'Not found.'}
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    # Handle Django's PermissionDenied exception
    if isinstance(exc, PermissionDenied):
        data = {'detail': 'Permission denied.'}
        return Response(data, status=status.HTTP_403_FORBIDDEN)

    # Handle database ProtectedError (when trying to delete an object that has related objects)
    if isinstance(exc, ProtectedError):
        data = {'detail': 'Cannot delete this object because it is referenced by other objects.'}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # Handle any other exceptions
    if exc:
        data = {'detail': str(exc)}
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # If we get here, something unexpected happened
    return Response(
        {'detail': 'An unexpected error occurred.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )