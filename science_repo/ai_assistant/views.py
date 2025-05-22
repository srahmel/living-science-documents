from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import time
from .models import AIModel, AIPrompt, AICommentSuggestion, AIPromptLog, AIReference, AIFeedback
from .serializers import (
    AIModelSerializer, AIPromptSerializer, 
    AICommentSuggestionSerializer, AICommentSuggestionListSerializer,
    AIPromptLogSerializer, AIReferenceSerializer, AIFeedbackSerializer
)
from publications.models import DocumentVersion
from comments.models import Comment, CommentType, CommentAuthor


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit AI models and prompts.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users
        return request.user.is_staff


class AIModelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI models.
    """
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'version', 'provider']
    ordering_fields = ['name', 'version', 'created_at']
    ordering = ['-created_at']


class AIPromptViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI prompts.
    """
    queryset = AIPrompt.objects.all()
    serializer_class = AIPromptSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AICommentSuggestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI comment suggestions.
    """
    queryset = AICommentSuggestion.objects.all()
    serializer_class = AICommentSuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'section_reference']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AICommentSuggestionListSerializer
        return AICommentSuggestionSerializer

    def get_queryset(self):
        """
        Optionally filter AI comment suggestions by document_version, status, or ai_model.
        """
        queryset = AICommentSuggestion.objects.all()

        document_version = self.request.query_params.get('document_version', None)
        if document_version is not None:
            queryset = queryset.filter(document_version=document_version)

        status_param = self.request.query_params.get('status', None)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        ai_model = self.request.query_params.get('ai_model', None)
        if ai_model is not None:
            queryset = queryset.filter(ai_model=ai_model)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an AI comment suggestion and create a real comment.
        """
        suggestion = self.get_object()

        # Check if the suggestion is pending
        if suggestion.status != 'pending':
            return Response({'detail': 'Only pending suggestions can be approved.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create a Scientific Comment type
        comment_type, created = CommentType.objects.get_or_create(
            code='SC',
            defaults={
                'name': 'Scientific Comment',
                'description': 'A scientific comment on the document content',
                'requires_doi': True
            }
        )

        # Create a new comment
        comment = Comment.objects.create(
            document_version=suggestion.document_version,
            comment_type=comment_type,
            content=suggestion.content,
            section_reference=suggestion.section_reference,
            line_start=suggestion.line_start,
            line_end=suggestion.line_end,
            status='draft',
            is_ai_generated=True
        )

        # Create a comment author entry for the current user
        CommentAuthor.objects.create(
            comment=comment,
            user=request.user,
            is_corresponding=True
        )

        # Update the suggestion
        suggestion.status = 'approved'
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = request.user
        suggestion.comment = comment
        suggestion.save()

        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject an AI comment suggestion.
        """
        suggestion = self.get_object()

        # Check if the suggestion is pending
        if suggestion.status != 'pending':
            return Response({'detail': 'Only pending suggestions can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the suggestion
        suggestion.status = 'rejected'
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = request.user
        suggestion.save()

        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def modify_and_approve(self, request, pk=None):
        """
        Modify and approve an AI comment suggestion.
        """
        suggestion = self.get_object()

        # Check if the suggestion is pending
        if suggestion.status != 'pending':
            return Response({'detail': 'Only pending suggestions can be modified and approved.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the modified content
        modified_content = request.data.get('content')
        if not modified_content:
            return Response({'detail': 'Modified content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create a Scientific Comment type
        comment_type, created = CommentType.objects.get_or_create(
            code='SC',
            defaults={
                'name': 'Scientific Comment',
                'description': 'A scientific comment on the document content',
                'requires_doi': True
            }
        )

        # Create a new comment
        comment = Comment.objects.create(
            document_version=suggestion.document_version,
            comment_type=comment_type,
            content=modified_content,
            section_reference=suggestion.section_reference,
            line_start=suggestion.line_start,
            line_end=suggestion.line_end,
            status='draft',
            is_ai_generated=True
        )

        # Create a comment author entry for the current user
        CommentAuthor.objects.create(
            comment=comment,
            user=request.user,
            is_corresponding=True
        )

        # Update the suggestion
        suggestion.status = 'modified'
        suggestion.reviewed_at = timezone.now()
        suggestion.reviewed_by = request.user
        suggestion.comment = comment
        suggestion.save()

        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate AI comment suggestions for a document version.
        """
        document_version_id = request.data.get('document_version')
        ai_model_id = request.data.get('ai_model')
        ai_prompt_id = request.data.get('ai_prompt')

        if not document_version_id or not ai_model_id or not ai_prompt_id:
            return Response({'detail': 'Document version, AI model, and AI prompt are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document_version = DocumentVersion.objects.get(id=document_version_id)
            ai_model = AIModel.objects.get(id=ai_model_id, is_active=True)
            ai_prompt = AIPrompt.objects.get(id=ai_prompt_id, is_active=True, ai_model=ai_model)
        except (DocumentVersion.DoesNotExist, AIModel.DoesNotExist, AIPrompt.DoesNotExist):
            return Response({'detail': 'Document version, AI model, or AI prompt not found.'}, status=status.HTTP_404_NOT_FOUND)

        # In a real implementation, this would call the AI service
        # For this example, we'll simulate AI-generated suggestions

        # Start timing for execution time measurement
        start_time = time.time()

        # Simulate AI processing
        suggestions = []

        # Create a suggestion for the introduction
        intro_suggestion = AICommentSuggestion.objects.create(
            document_version=document_version,
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            content="Could the introduction be strengthened by including more recent literature on the topic?",
            section_reference="Introduction",
            line_start=1,
            line_end=20,
            status='pending',
            confidence_score=0.85
        )
        suggestions.append(intro_suggestion)

        # Create a suggestion for the methodology
        method_suggestion = AICommentSuggestion.objects.create(
            document_version=document_version,
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            content="Is the sample size sufficient to support the conclusions drawn in the methodology section?",
            section_reference="Methodology",
            line_start=50,
            line_end=70,
            status='pending',
            confidence_score=0.92
        )
        suggestions.append(method_suggestion)

        # Create a reference for the methodology suggestion
        AIReference.objects.create(
            suggestion=method_suggestion,
            title="Statistical Power Analysis for the Behavioral Sciences",
            authors="Cohen, J.",
            publication_date=timezone.now().date(),
            citation_text="Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences. New York, NY: Routledge Academic",
            trust_level="high"
        )

        # End timing
        execution_time = time.time() - start_time

        # Log the prompt execution
        AIPromptLog.objects.create(
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            user=request.user,
            input_context=f"Document: {document_version.publication.title} v{document_version.version_number}",
            output_text="Generated 2 comment suggestions",
            execution_time=execution_time,
            token_count=500  # Simulated token count
        )

        serializer = AICommentSuggestionListSerializer(suggestions, many=True)
        return Response(serializer.data)


class AIPromptLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for AI prompt logs (read-only).
    """
    queryset = AIPromptLog.objects.all()
    serializer_class = AIPromptLogSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can view logs
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['input_context', 'output_text']
    ordering_fields = ['created_at', 'execution_time']
    ordering = ['-created_at']


class AIReferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI references.
    """
    queryset = AIReference.objects.all()
    serializer_class = AIReferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'authors', 'citation_text', 'doi']

    def get_queryset(self):
        """
        Optionally filter AI references by suggestion.
        """
        queryset = AIReference.objects.all()

        suggestion = self.request.query_params.get('suggestion', None)
        if suggestion is not None:
            queryset = queryset.filter(suggestion=suggestion)

        return queryset


class AIFeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for AI feedback.
    """
    queryset = AIFeedback.objects.all()
    serializer_class = AIFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see their own feedback.
        Admins can see all feedback.
        """
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset for schema generation
            return AIFeedback.objects.none()

        if self.request.user.is_staff:
            return AIFeedback.objects.all()
        return AIFeedback.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
