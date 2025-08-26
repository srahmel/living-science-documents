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
        fields = ['id', 'document_version', 'figure_number', 'title', 'caption', 'alt_text', 'license', 'source', 'attribution', 'image', 'created_at', 'updated_at']
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
                  'references', 'reviewer_response', 'metadata', 'release_date', 'status', 'status_date', 'status_user',
                  'authors', 'figures', 'tables', 'keywords', 'attachments', 'review_process',
                  'status_user_details']
        read_only_fields = ['id', 'doi', 'status_date', 'publication', 'version_number']

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
    # Add content fields from DocumentVersion
    content = serializers.SerializerMethodField()
    technical_abstract = serializers.SerializerMethodField()
    non_technical_abstract = serializers.SerializerMethodField()
    introduction = serializers.SerializerMethodField()
    methodology = serializers.SerializerMethodField()
    main_text = serializers.SerializerMethodField()
    conclusion = serializers.SerializerMethodField()
    author_contributions = serializers.SerializerMethodField()
    conflicts_of_interest = serializers.SerializerMethodField()
    acknowledgments = serializers.SerializerMethodField()
    funding = serializers.SerializerMethodField()
    references = serializers.SerializerMethodField()
    reviewer_response = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = ['id', 'meta_doi', 'title', 'short_title', 'created_at', 'updated_at', 
                  'status', 'editorial_board', 'document_versions', 'current_version',
                  'editorial_board_details', 'content', 'technical_abstract', 
                  'non_technical_abstract', 'introduction', 'methodology', 'main_text', 
                  'conclusion', 'author_contributions', 'conflicts_of_interest', 
                  'acknowledgments', 'funding', 'references', 'reviewer_response']
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

    # Helper method to get the latest version
    def _get_latest_version(self, obj):
        return obj.latest_version() or obj.current_version()

    # Methods to get content fields from the latest version
    def get_content(self, obj):
        version = self._get_latest_version(obj)
        return version.content if version else ""

    def get_technical_abstract(self, obj):
        version = self._get_latest_version(obj)
        return version.technical_abstract if version else ""

    def get_non_technical_abstract(self, obj):
        version = self._get_latest_version(obj)
        return version.non_technical_abstract if version else ""

    def get_introduction(self, obj):
        version = self._get_latest_version(obj)
        return version.introduction if version else ""

    def get_methodology(self, obj):
        version = self._get_latest_version(obj)
        return version.methodology if version else ""

    def get_main_text(self, obj):
        version = self._get_latest_version(obj)
        return version.main_text if version else ""

    def get_conclusion(self, obj):
        version = self._get_latest_version(obj)
        return version.conclusion if version else ""

    def get_author_contributions(self, obj):
        version = self._get_latest_version(obj)
        return version.author_contributions if version else ""

    def get_conflicts_of_interest(self, obj):
        version = self._get_latest_version(obj)
        return version.conflicts_of_interest if version else ""

    def get_acknowledgments(self, obj):
        version = self._get_latest_version(obj)
        return version.acknowledgments if version else ""

    def get_funding(self, obj):
        version = self._get_latest_version(obj)
        return version.funding if version else ""

    def get_references(self, obj):
        version = self._get_latest_version(obj)
        return version.references if version else ""

    def get_reviewer_response(self, obj):
        version = self._get_latest_version(obj)
        return version.reviewer_response if version else ""


class PublicationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing publications"""
    current_version_number = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = ['id', 'meta_doi', 'title', 'short_title', 'created_at', 
                  'status', 'current_version_number', 'authors', 'created_by', 'metadata']
        read_only_fields = ['id', 'created_at']

    def get_current_version_number(self, obj):
        current = obj.current_version()
        if current:
            return current.version_number
        return None

    def get_authors(self, obj):
        """Return authors from the latest version"""
        latest_version = obj.latest_version()
        if latest_version and latest_version.authors.exists():
            return AuthorSerializer(latest_version.authors.all(), many=True).data

        # If no authors or no version, include the editorial_board as a virtual author
        if obj.editorial_board:
            # Create a virtual author object with the editorial_board's information
            virtual_author = {
                'id': None,  # Not a real author record
                'name': obj.editorial_board.get_full_name() or obj.editorial_board.username,
                'address': None,
                'institution': obj.editorial_board.affiliation,
                'email': obj.editorial_board.email,
                'orcid': obj.editorial_board.orcid,
                'user': obj.editorial_board.id,
                'order': 0,
                'is_corresponding': True,
                'user_details': {
                    'id': obj.editorial_board.id,
                    'username': obj.editorial_board.username,
                    'full_name': obj.editorial_board.get_full_name(),
                    'orcid': obj.editorial_board.orcid
                }
            }
            return [virtual_author]

        return []

    def get_created_by(self, obj):
        """Return the user who created the publication"""
        # First try to get the user from the latest version's authors
        latest_version = obj.latest_version()
        if latest_version and latest_version.authors.filter(user__isnull=False).exists():
            author = latest_version.authors.filter(user__isnull=False).first()
            if author and author.user:
                return {
                    'id': author.user.id,
                    'username': author.user.username,
                    'full_name': author.user.get_full_name(),
                    'orcid': getattr(author.user, 'orcid', None)
                }

        # If no author with user is found, use the editorial_board as fallback
        if obj.editorial_board:
            return {
                'id': obj.editorial_board.id,
                'username': obj.editorial_board.username,
                'full_name': obj.editorial_board.get_full_name(),
                'orcid': getattr(obj.editorial_board, 'orcid', None)
            }

        return None

    def get_metadata(self, obj):
        """Return metadata from the latest version"""
        latest_version = obj.latest_version()
        if latest_version:
            return latest_version.metadata
        return None
