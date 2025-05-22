from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration
from .serializers import (
    CommentTypeSerializer, CommentSerializer, CommentListSerializer,
    CommentAuthorSerializer, CommentReferenceSerializer,
    ConflictOfInterestSerializer, CommentModerationSerializer
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