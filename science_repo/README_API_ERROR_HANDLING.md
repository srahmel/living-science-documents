# API Error Handling

## Overview

This document describes the error handling approach for the Living Science Documents API. The goal is to ensure that all API endpoints return JSON responses, even when errors occur.

## Problem

When an error occurs in a Django REST Framework (DRF) API, the default behavior depends on the `DEBUG` setting:

- When `DEBUG=True`, Django returns HTML error pages for exceptions, even for API requests.
- When `DEBUG=False`, DRF's default exception handler returns JSON responses for most errors, but some exceptions might still result in HTML responses.

This inconsistency can cause issues for frontend applications that expect JSON responses from all API endpoints.

## Solution

We've implemented a custom exception handler in `core/exceptions.py` that ensures all API endpoints return JSON responses, even when errors occur. The handler extends the default DRF exception handler to handle additional exceptions and ensure that all responses are in JSON format.

### Implementation

1. **Custom Exception Handler**: `core/exceptions.py` contains a custom exception handler that:
   - First tries the default DRF exception handler
   - Handles Django's `Http404` exception
   - Handles Django's `PermissionDenied` exception
   - Handles database `ProtectedError`
   - Handles any other exceptions

2. **Configuration**: The custom exception handler is configured in `settings.py`:
   ```python
   REST_FRAMEWORK = {
       # ... other settings ...
       'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
   }
   ```

3. **Testing**: The custom exception handler is tested in `core/tests_exceptions.py` to ensure that:
   - 404 errors return JSON responses
   - Method not allowed errors return JSON responses

## Response Format

All error responses follow this JSON format:

```json
{
    "detail": "Error message"
}
```

The HTTP status code is set appropriately based on the type of error:
- 404 for not found
- 403 for permission denied
- 400 for bad request
- 405 for method not allowed
- 500 for server errors

## Example

When a client requests a non-existent API endpoint:

```
GET /api/non-existent-endpoint/
```

The response will be:

```
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "detail": "Not found."
}
```

## Benefits

- Consistent response format for all API endpoints
- Better error handling for frontend applications
- Improved debugging experience