from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import Group
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration, CommentChat, ChatMessage
from .serializers import (
    CommentTypeSerializer, CommentSerializer, CommentListSerializer,
    CommentAuthorSerializer, CommentReferenceSerializer,
    ConflictOfInterestSerializer, CommentModerationSerializer,
    CommentChatSerializer, ChatMessageSerializer
)
from publications.models import DocumentVersion


class IsCommentatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users with the 'commentators' role to create comments.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to authenticated users in the 'commentators' group
        if request.user.is_authenticated:
            return request.user.groups.filter(name='commentators').exists()

        return False


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
    A user is considered a moderator for a comment if:
    1. They are assigned as a moderator to the document version associated with the comment, or
    2. They are a staff member
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff members can always moderate
        if request.user.is_staff:
            return True

        # Get the document version associated with the comment
        if hasattr(obj, 'document_version'):
            document_version = obj.document_version
        elif hasattr(obj, 'comment') and hasattr(obj.comment, 'document_version'):
            document_version = obj.comment.document_version
        else:
            return False

        # Check if the user is assigned as a moderator to this document version
        from publications.models import DocumentModerator
        return DocumentModerator.objects.filter(
            document_version=document_version,
            user=request.user,
            is_active=True
        ).exists()


class IsReviewEditorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow review editors to review comments.
    A user is considered a review editor for a comment if:
    1. They are assigned as a review editor to the document version associated with the comment, or
    2. They are a staff member
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff members can always review
        if request.user.is_staff:
            return True

        # Get the document version associated with the comment
        if hasattr(obj, 'document_version'):
            document_version = obj.document_version
        elif hasattr(obj, 'comment') and hasattr(obj.comment, 'document_version'):
            document_version = obj.comment.document_version
        else:
            return False

        # Check if the user is assigned as a review editor to this document version
        from publications.models import DocumentReviewEditor
        return DocumentReviewEditor.objects.filter(
            document_version=document_version,
            user=request.user,
            is_active=True
        ).exists()


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
    permission_classes = [IsCommentatorOrReadOnly, IsCommentAuthorOrReadOnly]
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
    permission_classes = [IsCommentatorOrReadOnly, IsCommentAuthorOrReadOnly]

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
    permission_classes = [IsCommentatorOrReadOnly, IsCommentAuthorOrReadOnly]
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
    permission_classes = [IsCommentatorOrReadOnly, IsCommentAuthorOrReadOnly]

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
        - Staff members can see all moderation entries
        - Moderators can see moderation entries for their assigned documents
        - Review editors can see moderation entries for their assigned documents
        - Authors can see moderation entries for their comments
        """
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset for schema generation
            return CommentModeration.objects.none()

        user = self.request.user

        # Staff members can see all
        if user.is_staff:
            return CommentModeration.objects.all()

        # Get documents where the user is assigned as a moderator
        from publications.models import DocumentModerator
        moderated_documents = DocumentModerator.objects.filter(
            user=user,
            is_active=True
        ).values_list('document_version', flat=True)

        # Get documents where the user is assigned as a review editor
        from publications.models import DocumentReviewEditor
        edited_documents = DocumentReviewEditor.objects.filter(
            user=user,
            is_active=True
        ).values_list('document_version', flat=True)

        # Combine the document lists
        assigned_documents = list(moderated_documents) + list(edited_documents)

        # Get comments for assigned documents
        if assigned_documents:
            assigned_comments = Comment.objects.filter(
                document_version__in=assigned_documents
            ).values_list('id', flat=True)

            # Return moderation entries for assigned comments
            moderation_for_assigned = CommentModeration.objects.filter(
                comment__in=assigned_comments
            )

            # Authors can also see moderation for their comments
            authored_comments = Comment.objects.filter(authors__user=user).values_list('id', flat=True)
            moderation_for_authored = CommentModeration.objects.filter(comment__in=authored_comments)

            # Combine the querysets
            return moderation_for_assigned | moderation_for_authored

        # If not a moderator or review editor, only show moderation for authored comments
        authored_comments = Comment.objects.filter(authors__user=user)
        return CommentModeration.objects.filter(comment__in=authored_comments)

    def perform_create(self, serializer):
        serializer.save(moderator=self.request.user, moderation_date=timezone.now())

    @action(detail=False, methods=['get'])
    def pending_comments(self, request):
        """
        Get comments pending moderation.
        """
        user = request.user

        # Staff members can see all pending comments
        if user.is_staff:
            pending_comments = Comment.objects.filter(
                status='submitted'
            ).exclude(
                id__in=CommentModeration.objects.values_list('comment_id', flat=True)
            )
            serializer = CommentListSerializer(pending_comments, many=True)
            return Response(serializer.data)

        # Get documents where the user is assigned as a moderator
        from publications.models import DocumentModerator
        moderated_documents = DocumentModerator.objects.filter(
            user=user,
            is_active=True
        ).values_list('document_version', flat=True)

        # Get documents where the user is assigned as a review editor
        from publications.models import DocumentReviewEditor
        edited_documents = DocumentReviewEditor.objects.filter(
            user=user,
            is_active=True
        ).values_list('document_version', flat=True)

        # Combine the document lists
        assigned_documents = list(moderated_documents) + list(edited_documents)

        if not assigned_documents:
            return Response({'detail': 'You are not assigned as a moderator or review editor to any documents.'}, 
                           status=status.HTTP_403_FORBIDDEN)

        # Get pending comments for assigned documents
        pending_comments = Comment.objects.filter(
            status='submitted',
            document_version__in=assigned_documents
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
        user = request.user
        comment_id = request.data.get('comment')

        if not comment_id:
            return Response({'detail': 'Comment ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(id=comment_id, status='submitted')
        except Comment.DoesNotExist:
            return Response({'detail': 'Comment not found or not in submitted status.'}, 
                           status=status.HTTP_404_NOT_FOUND)

        # Staff members can moderate any comment
        if not user.is_staff:
            # Check if the user is assigned as a moderator to this document
            from publications.models import DocumentModerator
            is_moderator = DocumentModerator.objects.filter(
                document_version=comment.document_version,
                user=user,
                is_active=True
            ).exists()

            # Check if the user is assigned as a review editor to this document
            from publications.models import DocumentReviewEditor
            is_review_editor = DocumentReviewEditor.objects.filter(
                document_version=comment.document_version,
                user=user,
                is_active=True
            ).exists()

            if not (is_moderator or is_review_editor):
                return Response(
                    {'detail': 'You are not assigned as a moderator or review editor to this document.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        decision = request.data.get('decision')
        decision_reason = request.data.get('decision_reason', '')

        if not decision:
            return Response({'detail': 'Decision is required.'}, status=status.HTTP_400_BAD_REQUEST)

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
