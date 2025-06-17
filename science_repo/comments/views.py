from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration, CommentChat, ChatMessage
from .serializers import (
    CommentTypeSerializer, CommentSerializer, CommentListSerializer,
    CommentAuthorSerializer, CommentReferenceSerializer,
    ConflictOfInterestSerializer, CommentModerationSerializer,
    CommentChatSerializer, ChatMessageSerializer
)
from publications.models import DocumentVersion


class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a comment to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the authors
        if hasattr(obj, 'authors'):
            # For Comment objects
            return obj.authors.filter(user=request.user).exists()
        elif hasattr(obj, 'comment') and hasattr(obj.comment, 'authors'):
            # For related objects like CommentReference, ConflictOfInterest, etc.
            return obj.comment.authors.filter(user=request.user).exists()

        return False


class IsModeratorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow moderators to moderate comments.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the user is a moderator (has moderated comments before)
        return CommentModeration.objects.filter(moderator=request.user).exists()


class CommentTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment types.
    """
    queryset = CommentType.objects.all()
    serializer_class = CommentTypeSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can manage comment types


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comments.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'referenced_text', 'section_reference', 'doi']
    ordering_fields = ['created_at', 'updated_at', 'status_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return CommentListSerializer
        return CommentSerializer

    def get_queryset(self):
        """
        Optionally filter comments by document_version, comment_type, or parent_comment.
        """
        queryset = Comment.objects.all()

        document_version = self.request.query_params.get('document_version', None)
        if document_version is not None:
            queryset = queryset.filter(document_version=document_version)

        comment_type = self.request.query_params.get('comment_type', None)
        if comment_type is not None:
            queryset = queryset.filter(comment_type__code=comment_type)

        parent_comment = self.request.query_params.get('parent_comment', None)
        if parent_comment is not None:
            if parent_comment == 'none':
                queryset = queryset.filter(parent_comment__isnull=True)
            else:
                queryset = queryset.filter(parent_comment=parent_comment)

        status_param = self.request.query_params.get('status', None)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        return queryset

    def perform_create(self, serializer):
        # Check if the document version has open discussions
        document_version_id = serializer.validated_data.get('document_version').id
        from publications.models import DocumentVersion
        from rest_framework.exceptions import ValidationError

        try:
            document_version = DocumentVersion.objects.get(id=document_version_id)
            if document_version.discussion_status != 'open':
                raise ValidationError(f"Cannot create comments for this document version. Discussion status is '{document_version.discussion_status}'.")
        except DocumentVersion.DoesNotExist:
            raise ValidationError("Document version not found.")

        comment = serializer.save(status='draft')

        # Create a CommentAuthor entry for the current user
        CommentAuthor.objects.create(
            comment=comment,
            user=self.request.user,
            is_corresponding=True
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit a comment for moderation.
        """
        comment = self.get_object()

        # Check if the user is an author
        if not comment.authors.filter(user=request.user).exists():
            return Response({'detail': 'Only authors can submit comments.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the comment is in draft status
        if comment.status != 'draft':
            return Response({'detail': 'Only draft comments can be submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate that SC and rSC comments are in question form
        if comment.comment_type.code in ['SC', 'rSC'] and not comment.is_question():
            return Response(
                {'detail': f"{comment.comment_type.code} comments must be in question form (end with '?')"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the status
        comment.status = 'submitted'
        comment.status_date = timezone.now()
        comment.status_user = request.user
        comment.save()

        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_chat(self, request, pk=None):
        """
        Create a chat for a comment.
        """
        comment = self.get_object()

        # Check if a chat already exists for this comment
        if hasattr(comment, 'chat'):
            return Response({'detail': 'Chat already exists for this comment.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new chat for the comment
        chat = CommentChat.objects.create(comment=comment)

        # If an initial message is provided, add it to the chat
        initial_message = request.data.get('initial_message')
        if initial_message:
            ChatMessage.objects.create(
                chat=chat,
                user=request.user,
                content=initial_message
            )

        serializer = CommentChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentAuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment authors.
    """
    queryset = CommentAuthor.objects.all()
    serializer_class = CommentAuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentAuthorOrReadOnly]

    def get_queryset(self):
        """
        Optionally filter comment authors by comment or user.
        """
        queryset = CommentAuthor.objects.all()

        comment = self.request.query_params.get('comment', None)
        if comment is not None:
            queryset = queryset.filter(comment=comment)

        user = self.request.query_params.get('user', None)
        if user is not None:
            queryset = queryset.filter(user=user)

        return queryset


class CommentReferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment references.
    """
    queryset = CommentReference.objects.all()
    serializer_class = CommentReferenceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'authors', 'citation_text', 'doi']

    def get_queryset(self):
        """
        Optionally filter comment references by comment.
        """
        queryset = CommentReference.objects.all()

        comment = self.request.query_params.get('comment', None)
        if comment is not None:
            queryset = queryset.filter(comment=comment)

        return queryset


class ConflictOfInterestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for conflicts of interest.
    """
    queryset = ConflictOfInterest.objects.all()
    serializer_class = ConflictOfInterestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentAuthorOrReadOnly]

    def get_queryset(self):
        """
        Optionally filter conflicts of interest by comment.
        """
        queryset = ConflictOfInterest.objects.all()

        comment = self.request.query_params.get('comment', None)
        if comment is not None:
            queryset = queryset.filter(comment=comment)

        return queryset


class CommentModerationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment moderation.
    """
    queryset = CommentModeration.objects.all()
    serializer_class = CommentModerationSerializer
    permission_classes = [permissions.IsAuthenticated, IsModeratorOrReadOnly]

    def get_queryset(self):
        """
        Filter moderation entries based on user role:
        - Moderators can see all moderation entries
        - Authors can see moderation entries for their comments
        """
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset for schema generation
            return CommentModeration.objects.none()

        user = self.request.user

        # Moderators can see all
        if CommentModeration.objects.filter(moderator=user).exists():
            return CommentModeration.objects.all()

        # Authors can see moderation for their comments
        authored_comments = Comment.objects.filter(authors__user=user)
        return CommentModeration.objects.filter(comment__in=authored_comments)

    def perform_create(self, serializer):
        serializer.save(moderator=self.request.user, moderation_date=timezone.now())

    @action(detail=False, methods=['get'])
    def pending_comments(self, request):
        """
        Get comments pending moderation.
        """
        # Check if the user is a moderator
        if not CommentModeration.objects.filter(moderator=request.user).exists():
            return Response({'detail': 'Only moderators can view pending comments.'}, status=status.HTTP_403_FORBIDDEN)

        # Get comments that are submitted but not yet moderated
        pending_comments = Comment.objects.filter(
            status='submitted'
        ).exclude(
            id__in=CommentModeration.objects.values_list('comment_id', flat=True)
        )

        serializer = CommentListSerializer(pending_comments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def moderate_comment(self, request):
        """
        Moderate a comment.
        """
        # Check if the user is a moderator
        if not CommentModeration.objects.filter(moderator=request.user).exists() and not request.user.is_staff:
            return Response({'detail': 'Only moderators can moderate comments.'}, status=status.HTTP_403_FORBIDDEN)

        comment_id = request.data.get('comment')
        decision = request.data.get('decision')
        decision_reason = request.data.get('decision_reason', '')

        if not comment_id or not decision:
            return Response({'detail': 'Comment ID and decision are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(id=comment_id, status='submitted')
        except Comment.DoesNotExist:
            return Response({'detail': 'Comment not found or not in submitted status.'}, status=status.HTTP_404_NOT_FOUND)

        # Create moderation entry
        moderation = CommentModeration.objects.create(
            comment=comment,
            moderator=request.user,
            decision=decision,
            decision_reason=decision_reason
        )

        # Update comment status based on decision
        if decision == 'approved':
            comment.status = 'published'
            # Generate DOI if required by comment type
            if comment.comment_type.requires_doi and not comment.doi:
                # This is a placeholder - in a real system, you would integrate with a DOI service
                comment.doi = f"10.1234/lsd.comment.{comment.id}"
        elif decision == 'rejected':
            comment.status = 'rejected'
        else:  # needs_revision
            comment.status = 'draft'

        comment.status_date = timezone.now()
        comment.status_user = request.user
        comment.save()

        serializer = self.get_serializer(moderation)
        return Response(serializer.data)


class CommentChatViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment chats.
    """
    queryset = CommentChat.objects.all()
    serializer_class = CommentChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter comment chats by comment.
        """
        queryset = CommentChat.objects.all()

        comment = self.request.query_params.get('comment', None)
        if comment is not None:
            queryset = queryset.filter(comment=comment)

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """
        Add a message to a comment chat.
        """
        chat = self.get_object()
        content = request.data.get('content')

        if not content:
            return Response({'detail': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        message = ChatMessage.objects.create(
            chat=chat,
            user=request.user,
            content=content
        )

        # Update the chat's updated_at timestamp
        chat.updated_at = timezone.now()
        chat.save()

        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for chat messages.
    """
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """
        Optionally filter chat messages by chat.
        """
        queryset = ChatMessage.objects.all()

        chat = self.request.query_params.get('chat', None)
        if chat is not None:
            queryset = queryset.filter(chat=chat)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
