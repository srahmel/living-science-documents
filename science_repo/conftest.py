import os
import threading
import time

# Ensure Django settings are configured for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'science_repo.settings')

import django

django.setup()

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from wsgiref.simple_server import make_server

_httpd = None
_server_thread = None


def pytest_sessionstart(session):
    """Initialize DB and start a local WSGI server on http://localhost:8000 for tests that call the API via requests."""
    global _httpd, _server_thread

    # Run migrations to ensure DB schema exists (works with SQLite in tests)
    try:
        call_command('migrate', interactive=False, verbosity=0)
    except Exception as e:
        # In case migrations fail, surface but don't crash immediate start
        print(f"[conftest] Warning: migrate failed: {e}")

    # Start WSGI server
    try:
        application = get_wsgi_application()
        _httpd = make_server('localhost', 8000, application)
        _server_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
        _server_thread.start()
        # small delay to ensure the server is ready
        time.sleep(0.2)
        print("[conftest] Test server started at http://localhost:8000/")
    except OSError as e:
        print(f"[conftest] Could not start test server on port 8000: {e}")


def pytest_sessionfinish(session, exitstatus):
    global _httpd
    if _httpd is not None:
        try:
            _httpd.shutdown()
            print("[conftest] Test server shut down.")
        except Exception as e:
            print(f"[conftest] Error shutting down server: {e}")
