from rest_framework import serializers
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration
from django.contrib.auth import get_user_model
from publications.serializers import DocumentVersionListSerializer

User = get_user_model()

class CommentTypeSerializer(serializers.ModelSerializer):
    """Serializer for the CommentType model"""
    class Meta:
        model = CommentType
        fields = ['id', 'code', 'name', 'description', 'requires_doi']
        read_only_fields = ['id']


class CommentReferenceSerializer(serializers.ModelSerializer):
    """Serializer for the CommentReference model"""
    class Meta:
        model = CommentReference
        fields = ['id', 'comment', 'title', 'authors', 'publication_date', 'doi', 
                  'url', 'citation_text', 'trust_level']
        read_only_fields = ['id']


class ConflictOfInterestSerializer(serializers.ModelSerializer):
    """Serializer for the ConflictOfInterest model"""
    class Meta:
        model = ConflictOfInterest
        fields = ['id', 'comment', 'statement', 'has_conflict']
        read_only_fields = ['id']


class CommentModerationSerializer(serializers.ModelSerializer):
    """Serializer for the CommentModeration model"""
    moderator_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentModeration
        fields = ['id', 'comment', 'moderator', 'moderation_date', 'decision', 
                  'decision_reason', 'moderator_details']
        read_only_fields = ['id', 'moderation_date']
    
    def get_moderator_details(self, obj):
        return {
            'id': obj.moderator.id,
            'username': obj.moderator.username,
            'full_name': obj.moderator.get_full_name()
        }


class CommentAuthorSerializer(serializers.ModelSerializer):
    """Serializer for the CommentAuthor model"""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentAuthor
        fields = ['id', 'comment', 'user', 'is_corresponding', 'created_at', 'user_details']
        read_only_fields = ['id', 'created_at']
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'orcid': obj.user.orcid,
            'affiliation': obj.user.affiliation
        }


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for the Comment model"""
    authors = CommentAuthorSerializer(many=True, read_only=True)
    references = CommentReferenceSerializer(many=True, read_only=True)
    conflict_of_interest = ConflictOfInterestSerializer(read_only=True)
    moderation = CommentModerationSerializer(read_only=True)
    comment_type_details = serializers.SerializerMethodField()
    document_version_details = serializers.SerializerMethodField()
    parent_comment_details = serializers.SerializerMethodField()
    status_user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'document_version', 'parent_comment', 'comment_type', 'content',
                  'referenced_text', 'section_reference', 'line_start', 'line_end', 'doi',
                  'status', 'created_at', 'updated_at', 'status_date', 'status_user',
                  'is_ai_generated', 'authors', 'references', 'conflict_of_interest',
                  'moderation', 'comment_type_details', 'document_version_details',
                  'parent_comment_details', 'status_user_details']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_date', 'doi']
    
    def get_comment_type_details(self, obj):
        return {
            'id': obj.comment_type.id,
            'code': obj.comment_type.code,
            'name': obj.comment_type.name
        }
    
    def get_document_version_details(self, obj):
        return {
            'id': obj.document_version.id,
            'publication_id': obj.document_version.publication.id,
            'publication_title': obj.document_version.publication.title,
            'version_number': obj.document_version.version_number,
            'doi': obj.document_version.doi
        }
    
    def get_parent_comment_details(self, obj):
        if obj.parent_comment:
            return {
                'id': obj.parent_comment.id,
                'comment_type': obj.parent_comment.comment_type.code,
                'doi': obj.parent_comment.doi
            }
        return None
    
    def get_status_user_details(self, obj):
        if obj.status_user:
            return {
                'id': obj.status_user.id,
                'username': obj.status_user.username,
                'full_name': obj.status_user.get_full_name()
            }
        return None
    
    def validate(self, data):
        """
        Validate that comments are in question form if required by the comment type.
        """
        if 'content' in data and 'comment_type' in data:
            comment_type = data['comment_type']
            content = data['content'].strip()
            
            # Check if SC or rSC comment is in question form
            if comment_type.code in ['SC', 'rSC'] and not content.endswith('?'):
                raise serializers.ValidationError(
                    f"{comment_type.code} comments must be in question form (end with '?')"
                )
        
        return data


class CommentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing comments"""
    comment_type_code = serializers.SerializerMethodField()
    author_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'document_version', 'comment_type_code', 'content', 'doi',
                  'status', 'created_at', 'is_ai_generated', 'author_count']
        read_only_fields = ['id', 'created_at', 'doi']
    
    def get_comment_type_code(self, obj):
        return obj.comment_type.code
    
    def get_author_count(self, obj):
        return obj.authors.count()