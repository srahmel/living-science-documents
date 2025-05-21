import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response


class ORCIDAuth:
    @staticmethod
    def get_auth_url(redirect_uri):
        return (f"{settings.ORCID_AUTH_URL}?"
                f"client_id={settings.ORCID_CLIENT_ID}&"
                f"response_type=code&"
                f"scope=/authenticate&"
                f"redirect_uri={redirect_uri}")

    @staticmethod
    def get_token(code, redirect_uri):
        data = {
            'client_id': settings.ORCID_CLIENT_ID,
            'client_secret': settings.ORCID_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }

        response = requests.post(settings.ORCID_TOKEN_URL, data=data)

        if response.status_code != 200:
            raise ValidationError('Failed to get ORCID token')

        return response.json()

    @staticmethod
    def get_orcid_profile(access_token):
        headers = {
            'Accept': 'application/vnd.orcid+json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(
            f'{settings.ORCID_API_URL}/person',
            headers=headers
        )

        if response.status_code != 200:
            raise ValidationError('Failed to get ORCID profile')

        return response.json()