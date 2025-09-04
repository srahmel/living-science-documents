from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import Group
from .models import AuditLog
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from .orcid import ORCIDAuth
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, LoginSerializer, RegistrationSerializer
from .analytics import AnalyticsService
from django.contrib.auth.models import Group
from django.urls import reverse
from django.middleware.csrf import get_token
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .email import EmailService

User = get_user_model()


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            description="Authentication successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User data')
                }
            )
        ),
        401: "Unauthorized",
        400: "Bad Request"
    },
    operation_description="Login with username and password to get JWT tokens."
)
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

    # Format errors as {"error": "Error description"}
    error_messages = []
    for field, errors in serializer.errors.items():
        for error in errors:
            error_messages.append(f"{error}")

    error_message = " ".join(error_messages)
    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)


class IsAdminOrEditorialOffice(permissions.BasePermission):
    """Allow only is_superuser or members of 'editorial_office' group."""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name='editorial_office').exists()


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


class RoleManagementView(generics.GenericAPIView):
    permission_classes = [IsAdminOrEditorialOffice]

    @swagger_auto_schema(
        operation_description="List available roles (groups) and a user's current roles.",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description='User ID to fetch roles for', type=openapi.TYPE_INTEGER, required=False)
        ]
    )
    def get(self, request, *args, **kwargs):
        user_id = request.GET.get('user_id')
        roles = list(Group.objects.values_list('name', flat=True))
        current = []
        if user_id:
            try:
                u = get_user_model().objects.get(id=user_id)
                current = list(u.groups.values_list('name', flat=True))
            except get_user_model().DoesNotExist:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'roles': roles, 'current': current})

    @swagger_auto_schema(
        operation_description="Assign or remove a role (group) to/from a user. Audited.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'role', 'action'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Group name'),
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['add', 'remove'])
            }
        )
    )
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        action = request.data.get('action')
        if not user_id or not role or action not in ['add', 'remove']:
            return Response({'detail': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response({'detail': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

        before = list(target_user.groups.values_list('name', flat=True))
        if action == 'add':
            target_user.groups.add(group)
            act = 'role_add'
        else:
            target_user.groups.remove(group)
            act = 'role_remove'
        after = list(target_user.groups.values_list('name', flat=True))

        # Audit log entry
        AuditLog.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            action=act,
            target_model='core.User',
            target_id=str(target_user.id),
            before_data={'groups': before},
            after_data={'groups': after},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        return Response({'detail': 'ok', 'before': before, 'after': after})

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        return super().get_object()


class AuditLogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = None  # use bare dicts

    @swagger_auto_schema(
        operation_description="List audit log entries (admin only)."
    )
    def get(self, request, *args, **kwargs):
        logs = AuditLog.objects.all()[:200]
        data = [
            {
                'id': log.id,
                'created_at': log.created_at,
                'actor': log.actor_id,
                'action': log.action,
                'target_model': log.target_model,
                'target_id': log.target_id,
                'before_data': log.before_data,
                'after_data': log.after_data,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
            }
            for log in logs
        ]
        return Response({'results': data})



@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="ORCID authentication URL",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'auth_url': openapi.Schema(type=openapi.TYPE_STRING, description='URL to redirect to for ORCID authentication')
                }
            )
        )
    },
    operation_description="Get the ORCID authentication URL for user login/registration."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def orcid_login(request):
    """
    Get the ORCID authentication URL.

    This endpoint returns a URL that the client should redirect to for ORCID authentication.

    Returns:
    - 200 OK: Returns the ORCID authentication URL
    """
    callback_url = reverse('orcid_callback')
    redirect_uri = request.build_absolute_uri(callback_url)

    # Generate state for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    request.session['orcid_oauth_state'] = state

    # Decide scope: if only Public API credentials, use /authenticate
    scope = "/authenticate"
    auth_url = ORCIDAuth.get_auth_url(redirect_uri, scope=scope) + f"&state={state}"
    return Response({'auth_url': auth_url, 'state': state})


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            name='code',
            in_=openapi.IN_QUERY,
            description='Authorization code from ORCID',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        302: "Redirect to frontend with JWT tokens",
        400: "Bad Request"
    },
    operation_description="Handle the ORCID authentication callback after user authorization."
)
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
        incoming_state = request.GET.get('state')
        # Determine if client expects JSON (AJAX/frontend callback)
        accept_hdr = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        wants_json = ('application/json' in accept_hdr) or (request.GET.get('format') == 'json') or is_ajax
        allow_stateless = getattr(settings, 'ORCID_ALLOW_STATELESS_CALLBACK', False) and wants_json

        # Validate state to prevent CSRF unless explicitly allowed for stateless JSON callback
        expected_state = request.session.get('orcid_oauth_state')
        if not code:
            return Response({'error': 'Missing authorization code'}, status=status.HTTP_400_BAD_REQUEST)
        if not allow_stateless:
            if not incoming_state or not expected_state or incoming_state != expected_state:
                return Response({'error': 'Invalid OAuth state or missing state'}, status=status.HTTP_400_BAD_REQUEST)
            # One-time use: clear state
            try:
                del request.session['orcid_oauth_state']
            except KeyError:
                pass

        callback_url = reverse('orcid_callback')
        redirect_uri = request.build_absolute_uri(callback_url)

        # Get ORCID token
        token_data = ORCIDAuth.get_token(code, redirect_uri)
        orcid_id = token_data['orcid']
        access_token = token_data['access_token']
        # Validate ORCID checksum
        if not ORCIDAuth.validate_orcid_checksum(orcid_id):
            return Response({'error': 'Invalid ORCID iD checksum'}, status=status.HTTP_400_BAD_REQUEST)

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

        # Assign user to the commentators group if created
        if created:
            from django.contrib.auth.models import Group
            commentators_group, created_group = Group.objects.get_or_create(name='commentators')
            user.groups.add(commentators_group)

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

        # If JSON requested, return tokens and user; else redirect to frontend with tokens
        accept = request.headers.get('Accept', '')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        wants_json = ('application/json' in accept) or (request.GET.get('format') == 'json') or is_ajax
        if wants_json:
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

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


@swagger_auto_schema(
    method='post',
    request_body=RegistrationSerializer,
    responses={
        201: openapi.Response(
            description="Registration successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User data')
                }
            )
        ),
        400: "Bad Request"
    },
    operation_description="Register a new user with username, password, and other required fields."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user.

    This endpoint allows users to register with a username, password, and other required fields.
    New users are automatically assigned to the 'commentators' group.

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

        # Assign user to the commentators group
        commentators_group, created = Group.objects.get_or_create(name='commentators')
        user.groups.add(commentators_group)

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

    # Format errors as {"error": "Error description"}
    error_messages = []
    for field, errors in serializer.errors.items():
        for error in errors:
            error_messages.append(f"{error}")

    error_message = " ".join(error_messages)
    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="CSRF token",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'csrfToken': openapi.Schema(type=openapi.TYPE_STRING, description='CSRF token')
                }
            )
        )
    },
    operation_description="Get a CSRF token for use in frontend applications."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """
    Get a CSRF token.

    This endpoint returns a CSRF token that can be used by frontend applications
    to make requests that require CSRF protection.
    This endpoint is publicly accessible without authentication.

    Returns:
    - 200 OK: Returns the CSRF token
    """
    token = get_token(request)
    return Response({'csrfToken': token})

# Create a separate public CSRF token view that explicitly bypasses authentication
class PublicCSRFTokenView(generics.GenericAPIView):
    """
    Public API view for getting a CSRF token without authentication.
    
    This view explicitly sets permission_classes to AllowAny to ensure
    it's publicly accessible regardless of global authentication settings.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Get a CSRF token without authentication.
        
        Returns:
        - 200 OK: Returns the CSRF token
        """
        token = get_token(request)
        return Response({'csrfToken': token})


@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response(
            description="Logout successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                }
            )
        ),
        401: "Unauthorized"
    },
    operation_description="Logout the current user by blacklisting their refresh token."
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout the current user.

    This endpoint blacklists the user's refresh token, effectively logging them out.
    The client should also remove any stored tokens.

    Returns:
    - 200 OK: Logout successful
    - 401 Unauthorized: If the user is not authenticated
    """
    try:
        # Get all outstanding tokens for the user
        tokens = OutstandingToken.objects.filter(user_id=request.user.id)
        
        # Blacklist all outstanding tokens
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
            
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email')
        },
        required=['email']
    ),
    responses={
        200: openapi.Response(
            description="Password reset email sent",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                }
            )
        ),
        400: "Bad Request",
        404: "User not found"
    },
    operation_description="Request a password reset email."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request a password reset email.
    
    This endpoint sends a password reset email to the user with the provided email address.
    The email contains a link with a token that can be used to reset the password.
    
    Parameters:
    - email: User's email address
    
    Returns:
    - 200 OK: Password reset email sent
    - 400 Bad Request: Invalid input data
    - 404 Not Found: User not found
    """
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Combine uid and token for security
        reset_token = f"{uid}-{token}"
        
        # Send password reset email
        EmailService.send_password_reset_email(user, reset_token)
        
        return Response({"detail": "Password reset email has been sent."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        # For security reasons, don't reveal that the user doesn't exist
        return Response({"detail": "Password reset email has been sent if the email exists."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='Password reset token'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password')
        },
        required=['token', 'email', 'password']
    ),
    responses={
        200: openapi.Response(
            description="Password reset successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
                }
            )
        ),
        400: "Bad Request",
        404: "User not found"
    },
    operation_description="Reset password with token."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Reset password with token.
    
    This endpoint resets the user's password using the token from the password reset email.
    
    Parameters:
    - token: Password reset token
    - email: User's email address
    - password: New password
    
    Returns:
    - 200 OK: Password reset successful
    - 400 Bad Request: Invalid input data or token
    - 404 Not Found: User not found
    """
    token = request.data.get('token')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not token or not email or not password:
        return Response({"error": "Token, email, and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Split token into uid and token
        try:
            uid, token = token.split('-', 1)
            uid = force_str(urlsafe_base64_decode(uid))
            user_from_uid = User.objects.get(pk=uid)
            
            # Verify that the uid matches the email
            if user.pk != user_from_uid.pk:
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, User.DoesNotExist, TypeError):
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(password)
        user.save()
        
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
