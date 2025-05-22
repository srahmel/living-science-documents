from rest_framework import serializers
from .models import AIModel, AIPrompt, AICommentSuggestion, AIPromptLog, AIReference, AIFeedback
from django.contrib.auth import get_user_model
from publications.serializers import DocumentVersionListSerializer
from comments.serializers import CommentSerializer

User = get_user_model()

class AIModelSerializer(serializers.ModelSerializer):
    """Serializer for the AIModel model"""
    class Meta:
        model = AIModel
        fields = ['id', 'name', 'version', 'provider', 'api_endpoint', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIPromptSerializer(serializers.ModelSerializer):
    """Serializer for the AIPrompt model"""
    ai_model_details = serializers.SerializerMethodField()
    created_by_details = serializers.SerializerMethodField()

    class Meta:
        model = AIPrompt
        fields = ['id', 'name', 'description', 'prompt_template', 'ai_model', 'is_active', 
                  'created_at', 'updated_at', 'created_by', 'ai_model_details', 'created_by_details']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_ai_model_details(self, obj):
        return {
            'id': obj.ai_model.id,
            'name': obj.ai_model.name,
            'version': obj.ai_model.version,
            'provider': obj.ai_model.provider
        }

    def get_created_by_details(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'full_name': obj.created_by.get_full_name()
            }
        return None


class AIReferenceSerializer(serializers.ModelSerializer):
    """Serializer for the AIReference model"""
    class Meta:
        model = AIReference
        fields = ['id', 'suggestion', 'title', 'authors', 'publication_date', 'doi', 
                  'url', 'citation_text', 'trust_level']
        read_only_fields = ['id']


class AIFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for the AIFeedback model"""
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = AIFeedback
        fields = ['id', 'suggestion', 'user', 'rating', 'feedback_text', 'created_at', 'user_details']
        read_only_fields = ['id', 'created_at', 'user']

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name()
        }


class AIPromptLogSerializer(serializers.ModelSerializer):
    """Serializer for the AIPromptLog model"""
    ai_model_details = serializers.SerializerMethodField()
    ai_prompt_details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = AIPromptLog
        fields = ['id', 'ai_model', 'ai_prompt', 'user', 'input_context', 'output_text',
                  'execution_time', 'token_count', 'created_at', 'ai_model_details',
                  'ai_prompt_details', 'user_details']
        read_only_fields = ['id', 'created_at']

    def get_ai_model_details(self, obj):
        return {
            'id': obj.ai_model.id,
            'name': obj.ai_model.name,
            'version': obj.ai_model.version
        }

    def get_ai_prompt_details(self, obj):
        return {
            'id': obj.ai_prompt.id,
            'name': obj.ai_prompt.name
        }

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name()
        }


class AICommentSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for the AICommentSuggestion model"""
    ai_model_details = serializers.SerializerMethodField()
    ai_prompt_details = serializers.SerializerMethodField()
    document_version_details = serializers.SerializerMethodField()
    reviewed_by_details = serializers.SerializerMethodField()
    comment_details = serializers.SerializerMethodField()
    references = AIReferenceSerializer(many=True, read_only=True)
    feedback = AIFeedbackSerializer(many=True, read_only=True)

    class Meta:
        model = AICommentSuggestion
        fields = ['id', 'document_version', 'ai_model', 'ai_prompt', 'content',
                  'section_reference', 'line_start', 'line_end', 'status', 'created_at',
                  'reviewed_at', 'reviewed_by', 'comment', 'confidence_score',
                  'ai_model_details', 'ai_prompt_details', 'document_version_details',
                  'reviewed_by_details', 'comment_details', 'references', 'feedback']
        read_only_fields = ['id', 'created_at', 'reviewed_at']

    def get_ai_model_details(self, obj):
        return {
            'id': obj.ai_model.id,
            'name': obj.ai_model.name,
            'version': obj.ai_model.version,
            'provider': obj.ai_model.provider
        }

    def get_ai_prompt_details(self, obj):
        return {
            'id': obj.ai_prompt.id,
            'name': obj.ai_prompt.name
        }

    def get_document_version_details(self, obj):
        return {
            'id': obj.document_version.id,
            'publication_id': obj.document_version.publication.id,
            'publication_title': obj.document_version.publication.title,
            'version_number': obj.document_version.version_number,
            'doi': obj.document_version.doi
        }

    def get_reviewed_by_details(self, obj):
        if obj.reviewed_by:
            return {
                'id': obj.reviewed_by.id,
                'username': obj.reviewed_by.username,
                'full_name': obj.reviewed_by.get_full_name()
            }
        return None

    def get_comment_details(self, obj):
        if obj.comment:
            return {
                'id': obj.comment.id,
                'doi': obj.comment.doi,
                'status': obj.comment.status
            }
        return None


class AICommentSuggestionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing AI comment suggestions"""
    ai_model_name = serializers.SerializerMethodField()
    document_title = serializers.SerializerMethodField()
    reference_count = serializers.SerializerMethodField()

    class Meta:
        model = AICommentSuggestion
        fields = ['id', 'document_version', 'ai_model_name', 'content', 'status',
                  'created_at', 'confidence_score', 'document_title', 'reference_count']
        read_only_fields = ['id', 'created_at']

    def get_ai_model_name(self, obj):
        return f"{obj.ai_model.name} v{obj.ai_model.version}"

    def get_document_title(self, obj):
        return obj.document_version.publication.title

    def get_reference_count(self, obj):
        return obj.references.count()
