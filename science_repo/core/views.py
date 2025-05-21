from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .orcid import ORCIDAuth
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()



@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_login(request):
    redirect_uri = request.build_absolute_uri('/api/auth/orcid/callback')
    auth_url = ORCIDAuth.get_auth_url(redirect_uri)
    return Response({'auth_url': auth_url})


@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_callback(request):
    try:
        code = request.GET.get('code')
        redirect_uri = request.build_absolute_uri('/api/auth/orcid/callback')

        # Get ORCID token
        token_data = ORCIDAuth.get_token(code, redirect_uri)
        orcid_id = token_data['orcid']
        access_token = token_data['access_token']

        # Get ORCID profile
        profile = ORCIDAuth.get_orcid_profile(access_token)

        # Get or create user
        user, created = User.objects.get_or_create(
            orcid=orcid_id,
            defaults={
                'username': f'orcid_{orcid_id}',
                'email': profile.get('emails', [{}])[0].get('email', ''),
                'first_name': profile.get('name', {}).get('given-names', {}).get('value', ''),
                'last_name': profile.get('name', {}).get('family-name', {}).get('value', ''),
            }
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Redirect to frontend with tokens
        frontend_url = settings.FRONTEND_URL  # Sie müssen diese in settings.py definieren
        return redirect(f'{frontend_url}/login/success?'
                        f'access={str(refresh.access_token)}&'
                        f'refresh={str(refresh)}')

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )