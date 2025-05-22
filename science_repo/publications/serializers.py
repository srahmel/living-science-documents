from rest_framework import serializers
from .models import Publication, DocumentVersion, Author, Figure, Table, Keyword, Attachment, ReviewProcess, Reviewer
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for the Author model"""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = ['id', 'name', 'address', 'institution', 'email', 'orcid', 'user', 'order', 'is_corresponding', 'user_details']
        read_only_fields = ['id']
    
    def get_user_details(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'full_name': obj.user.get_full_name(),
                'orcid': obj.user.orcid
            }
        return None


class FigureSerializer(serializers.ModelSerializer):
    """Serializer for the Figure model"""
    class Meta:
        model = Figure
        fields = ['id', 'document_version', 'figure_number', 'title', 'caption', 'image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TableSerializer(serializers.ModelSerializer):
    """Serializer for the Table model"""
    class Meta:
        model = Table
        fields = ['id', 'document_version', 'table_number', 'title', 'caption', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class KeywordSerializer(serializers.ModelSerializer):
    """Serializer for the Keyword model"""
    class Meta:
        model = Keyword
        fields = ['id', 'document_version', 'keyword']
        read_only_fields = ['id']


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for the Attachment model"""
    class Meta:
        model = Attachment
        fields = ['id', 'document_version', 'title', 'description', 'file', 'file_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewerSerializer(serializers.ModelSerializer):
    """Serializer for the Reviewer model"""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Reviewer
        fields = ['id', 'review_process', 'user', 'invited_at', 'accepted_at', 'completed_at', 'is_active', 'user_details']
        read_only_fields = ['id', 'invited_at']
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'orcid': obj.user.orcid,
            'affiliation': obj.user.affiliation
        }


class ReviewProcessSerializer(serializers.ModelSerializer):
    """Serializer for the ReviewProcess model"""
    reviewers = ReviewerSerializer(many=True, read_only=True)
    handling_editor_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewProcess
        fields = ['id', 'document_version', 'handling_editor', 'start_date', 'end_date', 
                  'status', 'decision', 'reviewers', 'handling_editor_details']
        read_only_fields = ['id', 'start_date']
    
    def get_handling_editor_details(self, obj):
        if obj.handling_editor:
            return {
                'id': obj.handling_editor.id,
                'username': obj.handling_editor.username,
                'full_name': obj.handling_editor.get_full_name(),
                'orcid': obj.handling_editor.orcid
            }
        return None


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for the DocumentVersion model"""
    authors = AuthorSerializer(many=True, read_only=True)
    figures = FigureSerializer(many=True, read_only=True)
    tables = TableSerializer(many=True, read_only=True)
    keywords = KeywordSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    review_process = ReviewProcessSerializer(read_only=True)
    status_user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVersion
        fields = ['id', 'publication', 'version_number', 'doi', 'content', 'technical_abstract',
                  'non_technical_abstract', 'introduction', 'methodology', 'main_text', 'conclusion',
                  'author_contributions', 'conflicts_of_interest', 'acknowledgments', 'funding',
                  'references', 'metadata', 'release_date', 'status', 'status_date', 'status_user',
                  'authors', 'figures', 'tables', 'keywords', 'attachments', 'review_process',
                  'status_user_details']
        read_only_fields = ['id', 'doi', 'status_date']
    
    def get_status_user_details(self, obj):
        if obj.status_user:
            return {
                'id': obj.status_user.id,
                'username': obj.status_user.username,
                'full_name': obj.status_user.get_full_name()
            }
        return None


class DocumentVersionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing document versions"""
    class Meta:
        model = DocumentVersion
        fields = ['id', 'publication', 'version_number', 'doi', 'technical_abstract', 
                  'release_date', 'status', 'status_date']
        read_only_fields = ['id', 'doi', 'status_date']


class PublicationSerializer(serializers.ModelSerializer):
    """Serializer for the Publication model"""
    document_versions = DocumentVersionListSerializer(many=True, read_only=True)
    current_version = serializers.SerializerMethodField()
    editorial_board_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = ['id', 'meta_doi', 'title', 'short_title', 'created_at', 'updated_at', 
                  'status', 'editorial_board', 'document_versions', 'current_version',
                  'editorial_board_details']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_version(self, obj):
        current = obj.current_version()
        if current:
            return DocumentVersionListSerializer(current).data
        return None
    
    def get_editorial_board_details(self, obj):
        if obj.editorial_board:
            return {
                'id': obj.editorial_board.id,
                'username': obj.editorial_board.username,
                'full_name': obj.editorial_board.get_full_name()
            }
        return None


class PublicationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing publications"""
    current_version_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = ['id', 'meta_doi', 'title', 'short_title', 'created_at', 
                  'status', 'current_version_number']
        read_only_fields = ['id', 'created_at']
    
    def get_current_version_number(self, obj):
        current = obj.current_version()
        if current:
            return current.version_number
        return None