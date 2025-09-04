from django.utils.deprecation import MiddlewareMixin
from decouple import config


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Sets a Content-Security-Policy header that includes orcid.org in frame-src to
    avoid CSP errors when any part of the application attempts to display ORCID
    content in a frame or popup context interpreted as a frame.

    Note: If a reverse proxy or frontend already sets a CSP header, that header
    may take precedence (or be combined in a restrictive way). In such cases,
    adjust CSP where it is originally defined as well.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Base frame-src allowlist; configurable via env
        default_sources = [
            "'self'",
            "https://orcid.org",
            "https://sandbox.orcid.org",
        ]
        # Allow adding extra sources via env var (comma-separated)
        extra = config('CSP_FRAME_SRC_EXTRA', default='', cast=str)
        extra_list = [s.strip() for s in extra.split(',') if s.strip()] if extra else []
        self.frame_src = ' '.join(default_sources + extra_list)

        # Build a simple CSP; keep it minimal to avoid breaking existing assets
        # Extend safely via env if needed
        self.base_csp = config('CONTENT_SECURITY_POLICY_BASE', default="default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; connect-src 'self' https:; frame-src ")

    def process_response(self, request, response):
        # Only set CSP if not already present to avoid overriding stricter upstream policies
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = f"{self.base_csp}{self.frame_src}"
        return response
