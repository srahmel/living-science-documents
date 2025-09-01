from rest_framework import serializers
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration, CommentChat, ChatMessage
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
                  'decision_reason', 'moderator_details', 'checked_question_form', 'checked_sources', 'checked_anchor']
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
    chat_details = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'document_version', 'parent_comment', 'comment_type', 'content',
                  'referenced_text', 'section_reference', 'line_start', 'line_end', 'range_hash', 'doi',
                  'status', 'created_at', 'updated_at', 'status_date', 'status_user',
                  'is_ai_generated', 'authors', 'references', 'conflict_of_interest',
                  'moderation', 'comment_type_details', 'document_version_details',
                  'parent_comment_details', 'status_user_details', 'chat_details']
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_date', 'doi']

    def to_internal_value(self, data):
        """
        Handle the case where comment_type is provided as a string code instead of a primary key.
        Maps string values to the appropriate enum value.
        """
        if 'comment_type' in data and isinstance(data['comment_type'], str):
            # Make a mutable copy of the data
            data = data.copy()

            # Get the original comment_type string
            comment_type_str = data['comment_type']

            # Try direct lookup by code first (case insensitive)
            try:
                comment_type = CommentType.objects.get(code__iexact=comment_type_str)
                data['comment_type'] = comment_type.id
                return super().to_internal_value(data)
            except CommentType.DoesNotExist:
                # Continue with mapping if direct lookup fails
                pass

            # Convert to uppercase for mapping
            comment_type_str = comment_type_str.upper()

            # Map common variations to standard codes
            mapping = {
                'ERROR': CommentType.CodeChoices.ERROR_CORRECTION,
                'ERRORCORRECTION': CommentType.CodeChoices.ERROR_CORRECTION,
                'SCIENTIFIC': CommentType.CodeChoices.SCIENTIFIC_COMMENT,
                'SCIENTIFICCOMMENT': CommentType.CodeChoices.SCIENTIFIC_COMMENT,
                'RESPONSE': CommentType.CodeChoices.RESPONSE_TO_SC,
                'RESPONSETOSCIENTIFICCOMMENT': CommentType.CodeChoices.RESPONSE_TO_SC,
                'ADDITIONAL': CommentType.CodeChoices.ADDITIONAL_DATA,
                'ADDITIONALDATA': CommentType.CodeChoices.ADDITIONAL_DATA,
                'NEW': CommentType.CodeChoices.NEW_PUBLICATION,
                'NEWPUBLICATION': CommentType.CodeChoices.NEW_PUBLICATION,
            }

            # Try to map the string to a standard code
            mapped_code = None

            # Check if it's a direct match with an enum value
            for choice in CommentType.CodeChoices.values:
                if comment_type_str == choice:
                    mapped_code = choice
                    break

            # If not a direct match, check the mapping
            if not mapped_code:
                for key, value in mapping.items():
                    if comment_type_str.replace(' ', '').replace('_', '').startswith(key):
                        mapped_code = value
                        break

            if mapped_code:
                try:
                    # Try to get the CommentType by the mapped code
                    comment_type = CommentType.objects.get(code=mapped_code)
                    data['comment_type'] = comment_type.id
                except CommentType.DoesNotExist:
                    # If the code doesn't exist, let the default validation handle it
                    pass

        return super().to_internal_value(data)

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

    def get_chat_details(self, obj):
        """
        Get details about the chat associated with the comment, if one exists.
        """
        try:
            if hasattr(obj, 'chat'):
                chat = obj.chat
                message_count = chat.messages.count()
                latest_message = chat.messages.order_by('-created_at').first()

                return {
                    'id': chat.id,
                    'created_at': chat.created_at,
                    'updated_at': chat.updated_at,
                    'message_count': message_count,
                    'latest_message': {
                        'id': latest_message.id,
                        'content': latest_message.content[:50] + '...' if latest_message and len(latest_message.content) > 50 else latest_message.content if latest_message else None,
                        'user': {
                            'id': latest_message.user.id,
                            'username': latest_message.user.username,
                            'full_name': latest_message.user.get_full_name()
                        } if latest_message else None,
                        'created_at': latest_message.created_at if latest_message else None
                    } if latest_message else None,
                    'has_messages': message_count > 0
                }
            return None
        except Exception:
            # If there's any error, return None
            return None

    def validate(self, data):
        """
        Enforce question-form for all comments. Type-specific logic can extend here.
        """
        if 'content' in data:
            content = data['content'].strip()
            if not content.endswith('?'):
                raise serializers.ValidationError(
                    "All comments must be in question form (end with '?')"
                )
        return data


class CommentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing comments"""
    comment_type_code = serializers.SerializerMethodField()
    author_count = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    visual_code = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'document_version', 'comment_type_code', 'content', 'doi',
                  'status', 'created_at', 'is_ai_generated', 'author_count', 'authors',
                  'referenced_text', 'section_reference', 'line_start', 'line_end', 'range_hash',
                  'visual_code']
        read_only_fields = ['id', 'created_at', 'doi']

    def get_comment_type_code(self, obj):
        return obj.comment_type.code

    def get_author_count(self, obj):
        return obj.authors.count()

    def get_authors(self, obj):
        """Return a list of authors with their names and AIDs (user IDs)"""
        return [
            {
                'name': author.user.get_full_name(),
                'aid': author.user.id
            }
            for author in obj.authors.all()
        ]

    def get_visual_code(self, obj):
        # Visual code mapping: green/hellgrün/blau/hellblau/grau (EN: green/lightgreen/blue/lightblue/gray)
        if obj.status == 'rejected':
            return 'gray'
        if obj.status in ['draft', 'under_review']:
            return 'lightblue' if obj.is_ai_generated else 'blue'
        if obj.status == 'accepted':
            return 'lightgreen' if obj.is_ai_generated else 'green'
        return 'blue'


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for the ChatMessage model"""
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'chat', 'user', 'content', 'created_at', 'updated_at', 'user_details']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'orcid': getattr(obj.user, 'orcid', None),
            'affiliation': getattr(obj.user, 'affiliation', None)
        }


class CommentChatSerializer(serializers.ModelSerializer):
    """Serializer for the CommentChat model"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    comment_details = serializers.SerializerMethodField()

    class Meta:
        model = CommentChat
        fields = ['id', 'comment', 'created_at', 'updated_at', 'messages', 'comment_details']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_comment_details(self, obj):
        return {
            'id': obj.comment.id,
            'comment_type': obj.comment.comment_type.code,
            'content': obj.comment.content[:100] + '...' if len(obj.comment.content) > 100 else obj.comment.content
        }
