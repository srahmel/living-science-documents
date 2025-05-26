from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .orcid import ORCIDAuth
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, LoginSerializer, RegistrationSerializer
from .analytics import AnalyticsService
from django.contrib.auth.models import Group

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login with username and password.

    Returns JWT tokens for authentication.

    Parameters:
    - username: User's username
    - password: User's password

    Returns:
    - 200 OK: Authentication successful, returns refresh and access tokens
    - 401 Unauthorized: Invalid credentials
    - 400 Bad Request: Invalid input data
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.

    list:
    Return a list of all users (admin only).

    create:
    Create a new user (admin only).

    retrieve:
    Return the given user.
    Use 'me' as the ID to get the current authenticated user.

    update:
    Update the given user.

    partial_update:
    Partially update the given user.

    destroy:
    Delete the given user (admin only).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()



@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_login(request):
    """
    Get the ORCID authentication URL.

    This endpoint returns a URL that the client should redirect to for ORCID authentication.

    Returns:
    - 200 OK: Returns the ORCID authentication URL
    """
    redirect_uri = request.build_absolute_uri('/api/auth/orcid/callback')
    # Request read-limited scope to get more user information
    auth_url = ORCIDAuth.get_auth_url(redirect_uri, scope="/authenticate /read-limited")
    return Response({'auth_url': auth_url})


@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_callback(request):
    """
    Handle the ORCID authentication callback.

    This endpoint is called by ORCID after the user has authenticated.
    It exchanges the authorization code for an access token, retrieves the user's ORCID profile,
    creates or retrieves the user account, and redirects to the frontend with JWT tokens.

    Parameters:
    - code: The authorization code from ORCID (query parameter)

    Returns:
    - 302 Found: Redirects to the frontend with JWT tokens
    - 400 Bad Request: If there's an error in the ORCID authentication process
    """
    try:
        code = request.GET.get('code')
        redirect_uri = request.build_absolute_uri('/api/auth/orcid/callback')

        # Get ORCID token
        token_data = ORCIDAuth.get_token(code, redirect_uri)
        orcid_id = token_data['orcid']
        access_token = token_data['access_token']

        # Get ORCID profile
        profile = ORCIDAuth.get_orcid_profile(access_token)

        # Extract user information from profile
        user_info = ORCIDAuth.extract_user_info(profile)

        # Format ORCID ID for display
        formatted_orcid = ORCIDAuth.format_orcid_id(orcid_id)

        # Get or create user
        user, created = User.objects.get_or_create(
            orcid=orcid_id,
            defaults={
                'username': f'orcid_{orcid_id}',
                'email': user_info['email'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'description': user_info['biography'],
                'external_link': user_info['website'],
                'research_field': ', '.join(user_info['keywords']),
            }
        )

        # Update user information if not created
        if not created:
            # Only update fields that are not empty in the ORCID profile
            if user_info['email'] and not user.email:
                user.email = user_info['email']
            if user_info['first_name'] and not user.first_name:
                user.first_name = user_info['first_name']
            if user_info['last_name'] and not user.last_name:
                user.last_name = user_info['last_name']
            if user_info['biography'] and not user.description:
                user.description = user_info['biography']
            if user_info['website'] and not user.external_link:
                user.external_link = user_info['website']
            if user_info['keywords'] and not user.research_field:
                user.research_field = ', '.join(user_info['keywords'])

            user.save()

        # Assign user to the readers group if created
        if created:
            from django.contrib.auth.models import Group
            readers_group = Group.objects.get(name='readers')
            user.groups.add(readers_group)

        # Create aliases for other names
        from core.models import UserAlias
        for other_name in user_info['other_names']:
            if ' ' in other_name:
                first_name, last_name = other_name.rsplit(' ', 1)
            else:
                first_name, last_name = other_name, ''

            UserAlias.objects.get_or_create(
                user=user,
                first_name=first_name,
                last_name=last_name
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Send welcome email if user was created
        if created:
            from core.email import EmailService
            EmailService.send_welcome_email(user)

        # Redirect to frontend with tokens
        frontend_url = settings.FRONTEND_URL
        return redirect(f'{frontend_url}/login/success?'
                        f'access={str(refresh.access_token)}&'
                        f'refresh={str(refresh)}')

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_summary(request):
    """
    Get a summary of analytics data.

    This endpoint returns a summary of analytics data, including:
    - Number of users (total, by time period)
    - Number of documents (total, by status, by time period)
    - Number of comments (total, by status, by type, by time period)

    Returns:
    - 200 OK: Returns the analytics summary
    """
    summary = AnalyticsService.get_analytics_summary()
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_users(request):
    """
    Get analytics data for users.

    This endpoint returns analytics data for users, including:
    - Number of users (total, by time period)

    Parameters:
    - time_period: The time period to filter by (query parameter, 'day', 'week', 'month', 'year', 'all')

    Returns:
    - 200 OK: Returns the user analytics data
    """
    time_period = request.query_params.get('time_period')
    count = AnalyticsService.get_user_count(time_period)

    return Response({
        'count': count,
        'time_period': time_period or 'all',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_documents(request):
    """
    Get analytics data for documents.

    This endpoint returns analytics data for documents, including:
    - Number of documents (total, by status, by time period)

    Parameters:
    - time_period: The time period to filter by (query parameter, 'day', 'week', 'month', 'year', 'all')
    - status: The status to filter by (query parameter, 'draft', 'published', etc.)

    Returns:
    - 200 OK: Returns the document analytics data
    """
    time_period = request.query_params.get('time_period')
    status = request.query_params.get('status')
    count = AnalyticsService.get_document_count(time_period, status)

    return Response({
        'count': count,
        'time_period': time_period or 'all',
        'status': status or 'all',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_comments(request):
    """
    Get analytics data for comments.

    This endpoint returns analytics data for comments, including:
    - Number of comments (total, by status, by type, by time period)

    Parameters:
    - time_period: The time period to filter by (query parameter, 'day', 'week', 'month', 'year', 'all')
    - status: The status to filter by (query parameter, 'draft', 'published', etc.)
    - comment_type: The comment type to filter by (query parameter, 'SC', 'rSC', 'ER', 'AD', 'NP')

    Returns:
    - 200 OK: Returns the comment analytics data
    """
    time_period = request.query_params.get('time_period')
    status = request.query_params.get('status')
    comment_type = request.query_params.get('comment_type')
    count = AnalyticsService.get_comment_count(time_period, status, comment_type)

    return Response({
        'count': count,
        'time_period': time_period or 'all',
        'status': status or 'all',
        'comment_type': comment_type or 'all',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_document_views(request, document_version_id=None):
    """
    Get analytics data for document views.

    This endpoint returns analytics data for document views, including:
    - Number of document views (total, by document, by time period)

    Parameters:
    - document_version_id: The ID of the document version (optional)
    - time_period: The time period to filter by (query parameter, 'day', 'week', 'month', 'year', 'all')

    Returns:
    - 200 OK: Returns the document view analytics data
    """
    time_period = request.query_params.get('time_period')
    count = AnalyticsService.get_document_views(document_version_id, time_period)

    return Response({
        'count': count,
        'document_version_id': document_version_id,
        'time_period': time_period or 'all',
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user.

    This endpoint allows users to register with a username, password, and other required fields.
    New users are automatically assigned to the 'readers' group.

    Parameters:
    - username: User's username
    - password: User's password
    - password2: Password confirmation
    - email: User's email
    - first_name: User's first name
    - last_name: User's last name
    - dsgvo_consent: Whether the user has accepted the DSGVO terms (required)
    - affiliation: User's affiliation (optional)
    - research_field: User's research field (optional)
    - qualification: User's qualification (optional)

    Returns:
    - 201 Created: Registration successful, returns user data and tokens
    - 400 Bad Request: Invalid input data
    """
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Assign user to the readers group
        readers_group = Group.objects.get(name='readers')
        user.groups.add(readers_group)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Send welcome email
        from core.email import EmailService
        EmailService.send_welcome_email(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
