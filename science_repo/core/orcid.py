import requests
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ORCIDAuth:
    """
    Service for ORCID authentication and API operations.

    This service provides methods for:
    - Authenticating users with ORCID
    - Retrieving ORCID profiles and records
    - Formatting ORCID IDs for display
    """

    @staticmethod
    def get_auth_url(redirect_uri, scope=None):
        """
        Get the ORCID authentication URL.

        Args:
            redirect_uri (str): The URI to redirect to after authentication
            scope (str, optional): The scope of access to request
                                  (default: /authenticate)

        Returns:
            str: The ORCID authentication URL
        """
        scope = scope or "/authenticate /read-limited"

        return (f"{settings.ORCID_AUTH_URL}?"
                f"client_id={settings.ORCID_CLIENT_ID}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"redirect_uri={redirect_uri}")

    @staticmethod
    def get_token(code, redirect_uri):
        """
        Exchange an authorization code for an access token.

        Args:
            code (str): The authorization code from ORCID
            redirect_uri (str): The redirect URI used in the authentication request

        Returns:
            dict: The token response from ORCID

        Raises:
            ValidationError: If the token request fails
        """
        data = {
            'client_id': settings.ORCID_CLIENT_ID,
            'client_secret': settings.ORCID_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        logger.debug("ORCID get_token: POST %s (redirect_uri=%s)", settings.ORCID_TOKEN_URL, redirect_uri)
        response = requests.post(settings.ORCID_TOKEN_URL, data=data, timeout=10)
        if response.status_code != 200:
            detail = ''
            try:
                detail = response.text
            except Exception:
                pass
            logger.warning("ORCID get_token failed: status=%s body=%s", response.status_code, detail)
            raise ValidationError('Failed to get ORCID token')
        payload = response.json()
        logger.debug("ORCID get_token success: token_type=%s scope=%s orcid_present=%s", payload.get('token_type'), payload.get('scope'), bool(payload.get('orcid')))
        return payload

    @staticmethod
    def get_public_app_token():
        """
        Obtain an application access token with /read-public via client_credentials.
        This is used to read public records when the user token lacks read scopes.
        Returns:
            str: access token
        Raises:
            ValidationError: if token cannot be obtained
        """
        data = {
            'client_id': settings.ORCID_CLIENT_ID,
            'client_secret': settings.ORCID_CLIENT_SECRET,
            'grant_type': 'client_credentials',
            'scope': '/read-public',
        }
        headers = {'Accept': 'application/json'}
        logger.debug("ORCID get_public_app_token: POST %s for /read-public", settings.ORCID_TOKEN_URL)
        response = requests.post(settings.ORCID_TOKEN_URL, data=data, headers=headers, timeout=10)
        if response.status_code != 200:
            detail = ''
            try:
                detail = response.text
            except Exception:
                pass
            logger.warning("ORCID get_public_app_token failed: status=%s body=%s", response.status_code, detail)
            raise ValidationError(f'Failed to get ORCID public token (status {response.status_code}): {detail}')
        payload = response.json()
        token = payload.get('access_token')
        if not token:
            logger.warning("ORCID get_public_app_token: missing access_token in payload")
            raise ValidationError('Failed to get ORCID public token: missing access_token')
        logger.debug("ORCID get_public_app_token success: token_type=%s scope=%s", payload.get('token_type'), payload.get('scope'))
        return token

    @staticmethod
    def get_orcid_profile(access_token, orcid_id):
        """
        Get the ORCID profile ("person" endpoint) for a user.

        Args:
            access_token (str): The access token for the ORCID API
            orcid_id (str): The ORCID iD of the user (16 chars, may contain dashes)

        Returns:
            dict: The ORCID profile

        Raises:
            ValidationError: If the profile request fails
        """
        headers = {
            'Accept': 'application/vnd.orcid+json',
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{settings.ORCID_API_URL}/{orcid_id}/person'
        logger.debug("ORCID get_orcid_profile: GET %s with user token", url)
        response = requests.get(url, headers=headers, timeout=10)

        # If unauthorized with user token, try application public token fallback
        if response.status_code in (401, 403):
            logger.debug("ORCID get_orcid_profile: received %s, attempting fallback with app token", response.status_code)
            try:
                app_token = ORCIDAuth.get_public_app_token()
                app_headers = {
                    'Accept': 'application/vnd.orcid+json',
                    'Authorization': f'Bearer {app_token}'
                }
                response = requests.get(url, headers=app_headers, timeout=10)
                logger.debug("ORCID get_orcid_profile: fallback response status=%s", response.status_code)
            except Exception as e:
                logger.warning("ORCID get_orcid_profile fallback failed: %s", str(e))
                raise ValidationError(f'Failed to get ORCID profile (fallback failed): {str(e)}')

        if response.status_code != 200:
            # Include details for easier debugging
            detail = ''
            try:
                detail = response.text
            except Exception:
                detail = ''
            logger.warning("ORCID get_orcid_profile failed: status=%s body=%s", response.status_code, detail)
            raise ValidationError(f'Failed to get ORCID profile (status {response.status_code}): {detail}')

        logger.debug("ORCID get_orcid_profile success for %s", orcid_id)
        return response.json()

    @staticmethod
    def get_orcid_record(access_token, orcid_id):
        """
        Get the full ORCID record for a user.

        Args:
            access_token (str): The access token for the ORCID API
            orcid_id (str): The ORCID ID of the user

        Returns:
            dict: The ORCID record

        Raises:
            ValidationError: If the record request fails
        """
        headers = {
            'Accept': 'application/vnd.orcid+json',
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{settings.ORCID_API_URL}/{orcid_id}/record'
        logger.debug("ORCID get_orcid_record: GET %s with user token", url)
        response = requests.get(url, headers=headers, timeout=10)

        # Fallback with app token on 401/403
        if response.status_code in (401, 403):
            logger.debug("ORCID get_orcid_record: received %s, attempting fallback with app token", response.status_code)
            try:
                app_token = ORCIDAuth.get_public_app_token()
                app_headers = {
                    'Accept': 'application/vnd.orcid+json',
                    'Authorization': f'Bearer {app_token}'
                }
                response = requests.get(url, headers=app_headers, timeout=10)
                logger.debug("ORCID get_orcid_record: fallback response status=%s", response.status_code)
            except Exception as e:
                logger.warning("ORCID get_orcid_record fallback failed: %s", str(e))
                raise ValidationError(f'Failed to get ORCID record (fallback failed): {str(e)}')

        if response.status_code != 200:
            detail = ''
            try:
                detail = response.text
            except Exception:
                pass
            logger.warning("ORCID get_orcid_record failed: status=%s body=%s", response.status_code, detail)
            raise ValidationError(f'Failed to get ORCID record (status {response.status_code}): {detail}')

        logger.debug("ORCID get_orcid_record success for %s", orcid_id)
        return response.json()

    @staticmethod
    def get_orcid_works(access_token, orcid_id):
        """
        Get the works (publications) for a user.

        Args:
            access_token (str): The access token for the ORCID API
            orcid_id (str): The ORCID ID of the user

        Returns:
            dict: The ORCID works

        Raises:
            ValidationError: If the works request fails
        """
        headers = {
            'Accept': 'application/vnd.orcid+json',
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{settings.ORCID_API_URL}/{orcid_id}/works'
        logger.debug("ORCID get_orcid_works: GET %s with user token", url)
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            detail = ''
            try:
                detail = response.text
            except Exception:
                pass
            logger.warning("ORCID get_orcid_works failed: status=%s body=%s", response.status_code, detail)
            raise ValidationError('Failed to get ORCID works')

        logger.debug("ORCID get_orcid_works success for %s", orcid_id)
        return response.json()

    @staticmethod
    def format_orcid_id(orcid_id):
        """
        Format an ORCID ID for display according to ORCID guidelines.

        Args:
            orcid_id (str): The ORCID ID to format

        Returns:
            str: The formatted ORCID ID
        """
        if not orcid_id:
            return ""

        # Remove any non-alphanumeric characters
        orcid_id = ''.join(c for c in orcid_id if c.isalnum() or c == 'X' or c == 'x')

        # Format as XXXX-XXXX-XXXX-XXXX
        if len(orcid_id) == 16:
            return f"{orcid_id[0:4]}-{orcid_id[4:8]}-{orcid_id[8:12]}-{orcid_id[12:16]}"

        return orcid_id

    @staticmethod
    def get_orcid_url(orcid_id):
        """
        Get the URL for an ORCID ID.

        Args:
            orcid_id (str): The ORCID ID

        Returns:
            str: The URL for the ORCID ID
        """
        formatted_id = ORCIDAuth.format_orcid_id(orcid_id)
        return f"https://orcid.org/{formatted_id}"

    @staticmethod
    def validate_orcid_checksum(orcid_id: str) -> bool:
        """
        Validate an ORCID iD using the ISO/IEC 7064 11,2 checksum algorithm.
        Accepts formatted (with dashes) or unformatted IDs, with last char possibly 'X'.
        """
        if not orcid_id:
            return False
        # Strip non-alphanumerics
        raw = ''.join(c for c in orcid_id if c.isalnum())
        if len(raw) != 16:
            return False
        total = 0
        for ch in raw[:-1]:
            if not ch.isdigit():
                return False
            total = (total + int(ch)) * 2
        remainder = total % 11
        result = (12 - remainder) % 11
        check = 'X' if result == 10 else str(result)
        return check.upper() == raw[-1].upper()

    @staticmethod
    def extract_user_info(profile):
        """
        Extract user information from an ORCID profile.

        Args:
            profile (dict): The ORCID profile

        Returns:
            dict: The extracted user information
        """
        user_info = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'other_names': [],
            'biography': '',
            'keywords': [],
            'country': '',
            'website': '',
        }

        # Extract name
        if 'name' in profile:
            if 'given-names' in profile['name'] and 'value' in profile['name']['given-names']:
                user_info['first_name'] = profile['name']['given-names']['value']

            if 'family-name' in profile['name'] and 'value' in profile['name']['family-name']:
                user_info['last_name'] = profile['name']['family-name']['value']

        # Extract email
        if 'emails' in profile and profile['emails'].get('email'):
            for email in profile['emails']['email']:
                if email.get('primary', False) and email.get('email'):
                    user_info['email'] = email['email']
                    break

            # If no primary email, use the first one
            if not user_info['email'] and profile['emails']['email']:
                user_info['email'] = profile['emails']['email'][0].get('email', '')

        # Extract other names
        if 'other-names' in profile and 'other-name' in profile['other-names']:
            for other_name in profile['other-names']['other-name']:
                if 'content' in other_name:
                    user_info['other_names'].append(other_name['content'])

        # Extract biography
        if 'biography' in profile and 'content' in profile['biography']:
            user_info['biography'] = profile['biography']['content']

        # Extract keywords
        if 'keywords' in profile and 'keyword' in profile['keywords']:
            for keyword in profile['keywords']['keyword']:
                if 'content' in keyword:
                    user_info['keywords'].append(keyword['content'])

        # Extract country
        if 'addresses' in profile and 'address' in profile['addresses']:
            for address in profile['addresses']['address']:
                if 'country' in address and 'value' in address['country']:
                    user_info['country'] = address['country']['value']
                    break

        # Extract website
        if 'researcher-urls' in profile and 'researcher-url' in profile['researcher-urls']:
            for url in profile['researcher-urls']['researcher-url']:
                if 'url' in url and 'value' in url['url']:
                    user_info['website'] = url['url']['value']
                    break

        return user_info
