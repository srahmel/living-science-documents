from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.http import Http404
import os
import logging

logger = logging.getLogger(__name__)
from .models import Publication, DocumentVersion, Author, Figure, Table, Keyword, Attachment, ReviewProcess, Reviewer
from .serializers import (
    PublicationSerializer, PublicationListSerializer, 
    DocumentVersionSerializer, DocumentVersionListSerializer,
    AuthorSerializer, FigureSerializer, TableSerializer, 
    KeywordSerializer, AttachmentSerializer,
    ReviewProcessSerializer, ReviewerSerializer
)
from .ojs import OJSClient
from .import_service import ImportService
from .jats_converter import JATSConverter


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a document to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the authors
        if hasattr(obj, 'authors'):
            # For DocumentVersion objects
            return obj.authors.filter(user=request.user).exists()
        elif hasattr(obj, 'document_version'):
            # For related objects like Figure, Table, etc.
            return obj.document_version.authors.filter(user=request.user).exists()

        return False


class IsEditorialBoardOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow editorial board members to edit publications.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to editorial board
        if hasattr(obj, 'editorial_board'):
            # For Publication objects
            return obj.editorial_board == request.user
        elif hasattr(obj, 'publication') and hasattr(obj.publication, 'editorial_board'):
            # For DocumentVersion objects
            return obj.publication.editorial_board == request.user

        return False


class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow reviewers to edit their reviews.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the reviewer
        if hasattr(obj, 'user'):
            # For Reviewer objects
            return obj.user == request.user

        return False


class PublicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing publications.

    list:
    Return a list of all publications.

    create:
    Create a new publication.

    retrieve:
    Return the given publication.

    update:
    Update the given publication.

    partial_update:
    Partially update the given publication.

    destroy:
    Delete the given publication.

    versions:
    Return all versions of the given publication.

    current_version:
    Return the current version of the given publication.
    """
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEditorialBoardOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'short_title', 'meta_doi']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PublicationListSerializer
        return PublicationSerializer

    def perform_create(self, serializer):
        # First save the publication to get an ID
        publication = serializer.save(editorial_board=self.request.user)

        # If meta_doi is not provided, generate one using the publication ID
        if not publication.meta_doi:
            from core.doi import DOIService
            meta_doi = DOIService.generate_doi(entity_type='publication', entity_id=publication.id)
            publication.meta_doi = meta_doi
            publication.save()

        # Automatically create a draft version for the new publication
        from .models import DocumentVersion
        # Generate a DOI for the document version
        from core.doi import DOIService
        version_doi = DOIService.generate_doi(entity_type='document_version', entity_id=f"{publication.id}.1")

        # Create the draft version with empty content fields
        document_version = DocumentVersion.objects.create(
            publication=publication,
            version_number=1,
            doi=version_doi,
            content='',
            technical_abstract='',
            introduction='',
            methodology='',
            main_text='',
            conclusion='',
            author_contributions='',
            references='',
            status='draft',
            status_user=self.request.user,
            status_date=timezone.now()
        )

        # Automatically create an author entry for the user who created the publication
        from .models import Author
        Author.objects.create(
            document_version=document_version,
            user=self.request.user,
            name=self.request.user.get_full_name() or self.request.user.username,
            email=self.request.user.email,
            institution=getattr(self.request.user, 'affiliation', None),
            orcid=getattr(self.request.user, 'orcid', None),
            is_corresponding=True,
            order=0
        )

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions of a publication.
        """
        publication = self.get_object()
        versions = publication.document_versions.all()
        serializer = DocumentVersionListSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def current_version(self, request, pk=None):
        """
        Get the current version of a publication.

        If the user is an author of any version of the publication, is the editorial board member,
        is a staff/superuser, or is the creator of any version, they can see the latest version regardless of status.
        Otherwise, only the latest published version is returned.
        """
        publication = self.get_object()

        # Log the authentication information
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"current_version called for publication {publication.id}")
        logger.info(f"Authentication header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        logger.info(f"Auth object: {request.auth}")
        if request.user.is_authenticated:
            logger.info(f"User ID: {request.user.id}, Username: {request.user.username}")
        else:
            logger.info(f"User NOT identified")

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Check if the user is a staff member or superuser
            is_staff_or_superuser = request.user.is_staff or request.user.is_superuser
            logger.info(f"User is staff or superuser: {is_staff_or_superuser}")

            # Check if the user is the editorial board member
            is_editorial_board = (publication.editorial_board == request.user)
            logger.info(f"User is editorial board: {is_editorial_board}")

            # Check if the user is an author of any version of the publication
            is_author = False
            # Check if the user is the creator of any version of the publication
            is_creator = False
            # Check if the user is the creator of the publication itself
            # First try to get the user from the latest version's authors
            is_publication_creator = False
            latest_version = publication.latest_version()
            if latest_version:
                # Check if the user is an author of the latest version
                if latest_version.authors.filter(user=request.user).exists():
                    is_publication_creator = True
                    logger.info(f"User is an author of the latest version")

                # Check if the user is the status_user of the latest version
                if latest_version.status_user == request.user:
                    is_publication_creator = True
                    logger.info(f"User is the status_user of the latest version")

            # If not found as an author or status_user, check if the user is the editorial board
            if not is_publication_creator and publication.editorial_board == request.user:
                is_publication_creator = True
                logger.info(f"User is the editorial board of the publication")

            logger.info(f"User is publication creator: {is_publication_creator}")

            # Check all versions to see if the user is an author or creator of any of them
            all_versions = list(publication.document_versions.all())
            logger.info(f"Publication has {len(all_versions)} versions")

            for version in all_versions:
                logger.info(f"Checking version {version.id}, status: {version.status}")

                # Check if the user is an author of this version
                author_exists = version.authors.filter(user=request.user).exists()
                if author_exists:
                    is_author = True
                    logger.info(f"User is author of version {version.id}")
                else:
                    logger.info(f"User is NOT author of version {version.id}")

                # Check if the user is the creator of this version
                creator_match = (version.status_user == request.user)
                if creator_match:
                    is_creator = True
                    logger.info(f"User is creator of version {version.id}")
                else:
                    logger.info(f"User is NOT creator of version {version.id}")

                # Log the authors of this version
                authors = list(version.authors.all())
                logger.info(f"Version {version.id} has {len(authors)} authors")
                for author in authors:
                    logger.info(f"Author: {author.name}, user_id: {author.user_id if author.user else 'None'}")

                # If the user is either an author or a creator, we can break the loop
                if is_author or is_creator:
                    break

            # If the user is an author, creator, publication creator, editorial board member, or staff/superuser, 
            # return the latest version regardless of status
            if is_author or is_creator or is_publication_creator or is_editorial_board or is_staff_or_superuser:
                logger.info(f"User has access. is_author: {is_author}, is_creator: {is_creator}, is_publication_creator: {is_publication_creator}, is_editorial_board: {is_editorial_board}, is_staff_or_superuser: {is_staff_or_superuser}")
                # First try to get the latest version
                version = publication.latest_version()
                if version:
                    logger.info(f"Returning latest version: {version.id}, status: {version.status}")
                    serializer = DocumentVersionSerializer(version)
                    return Response(serializer.data)

                # If no latest version, try to get the current (published) version
                version = publication.current_version()
                if version:
                    logger.info(f"No latest version found, returning current published version: {version.id}, status: {version.status}")
                    serializer = DocumentVersionSerializer(version)
                    return Response(serializer.data)

                # If no versions found through the helper methods, try to get any version directly
                all_versions = list(publication.document_versions.all())
                if all_versions:
                    # Get the version with the highest version number
                    version = sorted(all_versions, key=lambda v: v.version_number, reverse=True)[0]
                    logger.info(f"Found version directly: {version.id}, status: {version.status}")
                    serializer = DocumentVersionSerializer(version)
                    return Response(serializer.data)

                # If no versions at all, but user has special access, return the full publication data
                logger.info("No versions found at all, but user has special access")
                # Create a serializer for the publication
                pub_serializer = PublicationSerializer(publication)
                # Return the full publication data
                return Response(pub_serializer.data)
            else:
                logger.info(f"User does not have special access. is_author: {is_author}, is_creator: {is_creator}, is_publication_creator: {is_publication_creator}, is_editorial_board: {is_editorial_board}, is_staff_or_superuser: {is_staff_or_superuser}")
        else:
            logger.info("User is not authenticated")

        # For non-authenticated users or users who are not authors or editorial board members,
        # return only the published version
        version = publication.current_version()
        if version:
            logger.info(f"Returning published version: {version.id}")
            serializer = DocumentVersionSerializer(version)
            return Response(serializer.data)

        # If no published version found, check if there are any versions at all
        all_versions = list(publication.document_versions.filter(status='published'))
        if all_versions:
            # Get the version with the highest version number
            version = sorted(all_versions, key=lambda v: v.version_number, reverse=True)[0]
            logger.info(f"Found published version directly: {version.id}, status: {version.status}")
            serializer = DocumentVersionSerializer(version)
            return Response(serializer.data)

        # Check if the user is an author, creator, editorial office member, or staff/superuser
        if request.user.is_authenticated:
            # Check if the user is a staff member or superuser
            is_staff_or_superuser = request.user.is_staff or request.user.is_superuser

            # Check if the user is the editorial board member
            is_editorial_board = (publication.editorial_board == request.user)

            # Check if the user is an author or creator of any version
            is_author = False
            is_creator = False
            all_versions = list(publication.document_versions.all())

            for version in all_versions:
                # Check if the user is an author of this version
                if version.authors.filter(user=request.user).exists():
                    is_author = True
                    break

                # Check if the user is the creator of this version
                if version.status_user == request.user:
                    is_creator = True
                    break

            # If the user has special access, return the full publication data
            if is_author or is_creator or is_editorial_board or is_staff_or_superuser:
                logger.info(f"User has special access in second check. is_author: {is_author}, is_creator: {is_creator}, is_editorial_board: {is_editorial_board}, is_staff_or_superuser: {is_staff_or_superuser}")

                # First try to get the latest version
                latest_version = publication.latest_version()
                if latest_version:
                    logger.info(f"User has special access, returning latest version: {latest_version.id}")
                    serializer = DocumentVersionSerializer(latest_version)
                    return Response(serializer.data)

                # If no latest version found, check if there are any versions at all
                all_versions = list(publication.document_versions.all())
                if all_versions:
                    # Get the version with the highest version number
                    version = sorted(all_versions, key=lambda v: v.version_number, reverse=True)[0]
                    logger.info(f"User has special access, found version directly: {version.id}, status: {version.status}")
                    serializer = DocumentVersionSerializer(version)
                    return Response(serializer.data)

                # If no versions at all, return the full publication data
                logger.info("No versions found at all, but user has special access in second check")
                # Create a serializer for the publication
                pub_serializer = PublicationSerializer(publication)
                # Return the full publication data
                return Response(pub_serializer.data)

        logger.info("No published version found")
        from core.exceptions import format_error_response
        return format_error_response('No published version found.', status.HTTP_404_NOT_FOUND)


class DocumentVersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for document versions.
    """
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['technical_abstract', 'non_technical_abstract', 'doi']
    ordering_fields = ['version_number', 'release_date', 'status_date']
    ordering = ['-version_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentVersionListSerializer
        return DocumentVersionSerializer

    def _create_document_version_if_not_exists(self, request, version_id):
        """
        Helper method to create a document version if it doesn't exist.
        Returns a tuple (document_version, response) where:
        - document_version is the created document version or None if it couldn't be created
        - response is a Response object if there was an error, or None if successful
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Document version with ID {version_id} not found, checking permissions to create one")

        # Check if the user is authenticated
        if not request.user.is_authenticated:
            logger.info("User is not authenticated")
            from core.exceptions import format_error_response
            return None, format_error_response('Document version not found.', status.HTTP_404_NOT_FOUND)

        # Get the document version ID
        if not version_id:
            logger.info("No version ID provided")
            from core.exceptions import format_error_response
            return None, format_error_response('No version ID provided.', status.HTTP_400_BAD_REQUEST)

        # Try to find the publication associated with this version ID
        # This is a simplification - in a real scenario, you might need to parse the ID
        # to extract the publication ID, or use a different approach
        try:
            # Assuming the version ID is a numeric value
            publication_id = int(version_id)
            publication = Publication.objects.get(id=publication_id)
            logger.info(f"Found publication with ID {publication_id}")
        except (ValueError, Publication.DoesNotExist):
            logger.info(f"Publication with ID {version_id} not found")
            from core.exceptions import format_error_response
            return None, format_error_response('Publication not found.', status.HTTP_404_NOT_FOUND)

        # Check if the user has appropriate permissions
        is_author = False
        is_creator = False
        is_editorial_board = (publication.editorial_board == request.user)
        is_staff_or_superuser = request.user.is_staff or request.user.is_superuser

        # Check if the user is an author or creator of any version of the publication
        all_versions = list(publication.document_versions.all())
        for version in all_versions:
            # Check if the user is an author of this version
            if version.authors.filter(user=request.user).exists():
                is_author = True
                break

            # Check if the user is the creator of this version
            if version.status_user == request.user:
                is_creator = True
                break

        # If the user has appropriate permissions, create a new document version
        if is_author or is_creator or is_editorial_board or is_staff_or_superuser:
            logger.info(f"User has appropriate permissions. is_author: {is_author}, is_creator: {is_creator}, is_editorial_board: {is_editorial_board}, is_staff_or_superuser: {is_staff_or_superuser}")

            # Generate a DOI for the document version
            from core.doi import DOIService
            version_number = 1
            latest_version = publication.document_versions.order_by('-version_number').first()
            if latest_version:
                version_number = latest_version.version_number + 1
            version_doi = DOIService.generate_doi(entity_type='document_version', entity_id=f"{publication.id}.{version_number}")

            # Create the document version
            document_version = DocumentVersion.objects.create(
                publication=publication,
                version_number=version_number,
                doi=version_doi,
                content='',
                technical_abstract='',
                introduction='',
                methodology='',
                main_text='',
                conclusion='',
                author_contributions='',
                references='',
                status='draft',
                status_user=request.user,
                status_date=timezone.now()
            )

            # Create an author entry for the user
            Author.objects.create(
                document_version=document_version,
                user=request.user,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                institution=getattr(request.user, 'affiliation', None),
                orcid=getattr(request.user, 'orcid', None),
                is_corresponding=True,
                order=0
            )

            logger.info(f"Created new document version with ID {document_version.id}")
            return document_version, None
        else:
            logger.info(f"User does not have appropriate permissions. is_author: {is_author}, is_creator: {is_creator}, is_editorial_board: {is_editorial_board}, is_staff_or_superuser: {is_staff_or_superuser}")
            from core.exceptions import format_error_response
            return None, format_error_response('Document version not found.', status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a document version.
        If the document version doesn't exist and the user has appropriate permissions
        (author, creator, or editorial office), create a new document version.
        """
        try:
            # Try to get the document version
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            # If the document version doesn't exist, try to create one
            document_version, error_response = self._create_document_version_if_not_exists(request, kwargs.get('pk'))
            if document_version:
                serializer = self.get_serializer(document_version)
                return Response(serializer.data)
            else:
                return error_response

    def update(self, request, *args, **kwargs):
        """
        Update a document version.
        If the document version doesn't exist and the user has appropriate permissions
        (author, creator, or editorial office), create a new document version and update it.
        """
        try:
            # Try to get the document version
            return super().update(request, *args, **kwargs)
        except Http404:
            # If the document version doesn't exist, try to create one
            document_version, error_response = self._create_document_version_if_not_exists(request, kwargs.get('pk'))
            if document_version:
                # Update the document version with the request data
                serializer = self.get_serializer(document_version, data=request.data, partial=False)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                return error_response

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a document version.
        If the document version doesn't exist and the user has appropriate permissions
        (author, creator, or editorial office), create a new document version and update it.
        """
        try:
            # Try to get the document version
            return super().partial_update(request, *args, **kwargs)
        except Http404:
            # If the document version doesn't exist, try to create one
            document_version, error_response = self._create_document_version_if_not_exists(request, kwargs.get('pk'))
            if document_version:
                # Update the document version with the request data
                serializer = self.get_serializer(document_version, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                return error_response

    def perform_update(self, serializer):
        """
        Custom perform_update method that creates a new version instead of updating the existing one
        when changes are detected.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Get the original instance
        instance = serializer.instance

        # Check if there are actual changes to the document
        has_changes = False
        for field_name, new_value in serializer.validated_data.items():
            # Skip status-related fields as they don't constitute content changes
            if field_name in ['status', 'status_date', 'status_user']:
                continue

            # Get the original value
            original_value = getattr(instance, field_name)

            # Compare the values
            if original_value != new_value:
                has_changes = True
                logger.info(f"Field '{field_name}' changed from '{original_value}' to '{new_value}'")
                break

        # If there are changes, create a new version
        if has_changes:
            logger.info(f"Changes detected in document version {instance.id}, creating a new version")

            # Get the publication
            publication = instance.publication

            # Set the version number automatically
            latest_version = publication.document_versions.order_by('-version_number').first()
            version_number = latest_version.version_number + 1

            # Generate a DOI for the new document version
            from core.doi import DOIService
            version_doi = DOIService.generate_doi(entity_type='document_version', entity_id=f"{publication.id}.{version_number}")

            # Create a new document version with the updated data
            new_instance = DocumentVersion.objects.create(
                publication=publication,
                version_number=version_number,
                doi=version_doi,
                content=serializer.validated_data.get('content', instance.content),
                technical_abstract=serializer.validated_data.get('technical_abstract', instance.technical_abstract),
                non_technical_abstract=serializer.validated_data.get('non_technical_abstract', instance.non_technical_abstract),
                introduction=serializer.validated_data.get('introduction', instance.introduction),
                methodology=serializer.validated_data.get('methodology', instance.methodology),
                main_text=serializer.validated_data.get('main_text', instance.main_text),
                conclusion=serializer.validated_data.get('conclusion', instance.conclusion),
                author_contributions=serializer.validated_data.get('author_contributions', instance.author_contributions),
                conflicts_of_interest=serializer.validated_data.get('conflicts_of_interest', instance.conflicts_of_interest),
                acknowledgments=serializer.validated_data.get('acknowledgments', instance.acknowledgments),
                funding=serializer.validated_data.get('funding', instance.funding),
                references=serializer.validated_data.get('references', instance.references),
                reviewer_response=serializer.validated_data.get('reviewer_response', instance.reviewer_response),
                metadata=serializer.validated_data.get('metadata', instance.metadata),
                release_date=serializer.validated_data.get('release_date', instance.release_date),
                status=serializer.validated_data.get('status', instance.status),
                status_user=self.request.user,
                status_date=timezone.now()
            )

            # Copy authors from the original version
            for author in instance.authors.all():
                Author.objects.create(
                    document_version=new_instance,
                    user=author.user,
                    name=author.name,
                    address=author.address,
                    institution=author.institution,
                    email=author.email,
                    orcid=author.orcid,
                    is_corresponding=author.is_corresponding,
                    order=author.order
                )

            # Copy figures from the original version
            for figure in instance.figures.all():
                Figure.objects.create(
                    document_version=new_instance,
                    figure_number=figure.figure_number,
                    title=figure.title,
                    caption=figure.caption,
                    image=figure.image
                )

            # Copy tables from the original version
            for table in instance.tables.all():
                Table.objects.create(
                    document_version=new_instance,
                    table_number=table.table_number,
                    title=table.title,
                    caption=table.caption,
                    content=table.content
                )

            # Copy keywords from the original version
            for keyword in instance.keywords.all():
                Keyword.objects.create(
                    document_version=new_instance,
                    keyword=keyword.keyword
                )

            # Copy attachments from the original version
            for attachment in instance.attachments.all():
                Attachment.objects.create(
                    document_version=new_instance,
                    title=attachment.title,
                    description=attachment.description,
                    file=attachment.file,
                    file_type=attachment.file_type
                )

            # Update the serializer instance to the new version
            serializer.instance = new_instance

            logger.info(f"Created new document version {new_instance.id} with version number {version_number}")

            return new_instance
        else:
            # If there are no changes, update the existing version
            logger.info(f"No changes detected in document version {instance.id}, updating existing version")
            return super().perform_update(serializer)

    def perform_create(self, serializer):
        # Get the publication ID from the request data or URL parameters
        publication_id = self.request.data.get('publication') or self.kwargs.get('publication_id')

        # If publication_id is not provided, raise an error
        if not publication_id:
            from core.exceptions import format_error_response
            raise serializers.ValidationError({'publication': ['This field is required.']})

        # Get the publication object
        publication = get_object_or_404(Publication, pk=publication_id)

        # Set the version number automatically
        latest_version = publication.document_versions.order_by('-version_number').first()
        version_number = 1
        if latest_version:
            version_number = latest_version.version_number + 1

        # Save the document version
        document_version = serializer.save(
            publication=publication,
            version_number=version_number,
            status_user=self.request.user,
            status_date=timezone.now()
        )

        # Automatically create an author entry for the user who created the document version
        # if no authors are specified in the request
        if not document_version.authors.exists():
            Author.objects.create(
                document_version=document_version,
                user=self.request.user,
                name=self.request.user.get_full_name() or self.request.user.username,
                email=self.request.user.email,
                institution=getattr(self.request.user, 'affiliation', None),
                orcid=getattr(self.request.user, 'orcid', None),
                is_corresponding=True,
                order=0
            )

        # Generate AI keywords for the new document version
        try:
            from ai_assistant.models import AIModel
            from ai_assistant.openai_service import OpenAIService

            # Get the default AI model
            ai_model = AIModel.objects.filter(is_active=True).first()

            if ai_model:
                # Generate keywords using AI
                OpenAIService.generate_keywords(
                    document_version=document_version,
                    ai_model=ai_model,
                    user=self.request.user
                )
        except Exception as e:
            # Log the error but don't fail the document creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating AI keywords: {str(e)}")

    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """
        Submit a document version for review.
        """
        document = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is an author
        if not document.authors.filter(user=request.user).exists():
            return format_error_response('Only authors can submit for review.', status.HTTP_403_FORBIDDEN)

        # Check if the document is in draft status
        if document.status != 'draft':
            return format_error_response('Only draft documents can be submitted for review.')

        # Update the status
        document.status = 'submitted'
        document.status_date = timezone.now()
        document.status_user = request.user
        document.save()

        # Create a review process if it doesn't exist
        ReviewProcess.objects.get_or_create(
            document_version=document,
            defaults={'status': 'pending'}
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_keywords(self, request, pk=None):
        """
        Generate AI keywords for a document version.
        """
        document = self.get_object()

        try:
            from ai_assistant.models import AIModel
            from ai_assistant.openai_service import OpenAIService

            # Get the default AI model
            ai_model = AIModel.objects.filter(is_active=True).first()

            if not ai_model:
                from core.exceptions import format_error_response
                return format_error_response('No active AI model found.')

            # Generate keywords using AI
            keywords = OpenAIService.generate_keywords(
                document_version=document,
                ai_model=ai_model,
                user=request.user,
                max_keywords=int(request.data.get('max_keywords', 5))
            )

            # Return the generated keywords
            from .serializers import KeywordSerializer
            serializer = KeywordSerializer(keywords, many=True)
            return Response(serializer.data)

        except Exception as e:
            from core.exceptions import format_error_response
            return format_error_response(f'Error generating keywords: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR, exc=e)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish a document version.

        When a new version is published, discussions on previous versions are automatically closed.
        """
        document = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the editorial board member
        if document.publication.editorial_board != request.user:
            return format_error_response('Only editorial board members can publish documents.', status.HTTP_403_FORBIDDEN)

        # Check if the document is in accepted status
        if document.status != 'accepted':
            return format_error_response('Only accepted documents can be published.')

        # Update the status
        document.status = 'published'
        document.status_date = timezone.now()
        document.status_user = request.user
        document.release_date = timezone.now().date()
        document.save()

        # Close discussions on previous versions of this publication
        previous_versions = document.publication.document_versions.filter(
            version_number__lt=document.version_number,
            discussion_status='open'
        )

        for prev_version in previous_versions:
            prev_version.discussion_status = 'closed'
            prev_version.discussion_closed_date = timezone.now()
            prev_version.discussion_closed_by = request.user
            prev_version.save()

            # Log the action
            logger.info(
                f"Discussions closed for {prev_version} due to new version {document.version_number} publication. "
                f"Closed by {request.user.username}."
            )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close_discussion(self, request, pk=None):
        """
        Close the discussion phase for a document version.

        This endpoint allows moderators to manually close the discussion phase for a document version.
        Only editorial board members or staff can close discussions.
        """
        document = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the editorial board member or staff
        if document.publication.editorial_board != request.user and not request.user.is_staff:
            return format_error_response('Only editorial board members or staff can close discussions.', status.HTTP_403_FORBIDDEN)

        # Check if the discussion is already closed
        if document.discussion_status != 'open':
            return format_error_response(f'Discussion is already {document.discussion_status}.', status.HTTP_400_BAD_REQUEST)

        # Close the discussion
        document.discussion_status = 'closed'
        document.discussion_closed_date = timezone.now()
        document.discussion_closed_by = request.user
        document.save()

        # Log the action
        logger.info(
            f"Discussions manually closed for {document} by {request.user.username}."
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """
        Withdraw a document version.

        This endpoint allows authors to withdraw their publication, which also closes the discussion phase.
        Only authors or editorial board members can withdraw publications.
        """
        document = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is an author or the editorial board member
        is_author = document.authors.filter(user=request.user).exists()
        is_editorial = document.publication.editorial_board == request.user

        if not (is_author or is_editorial or request.user.is_staff):
            return format_error_response('Only authors, editorial board members, or staff can withdraw publications.', 
                                        status.HTTP_403_FORBIDDEN)

        # Check if the document is already withdrawn
        if document.discussion_status == 'withdrawn':
            return format_error_response('Publication is already withdrawn.', status.HTTP_400_BAD_REQUEST)

        # Withdraw the publication and close discussions
        document.discussion_status = 'withdrawn'
        document.discussion_closed_date = timezone.now()
        document.discussion_closed_by = request.user

        # If the document is published, mark it as archived
        if document.status == 'published':
            document.status = 'archived'
            document.status_date = timezone.now()
            document.status_user = request.user

        document.save()

        # Log the action
        logger.info(
            f"Publication {document} withdrawn by {request.user.username}."
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for authors.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        # If the user is creating an author entry for themselves, link it to their user account
        if not serializer.validated_data.get('user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class FigureViewSet(viewsets.ModelViewSet):
    """
    API endpoint for figures.
    """
    queryset = Figure.objects.all()
    serializer_class = FigureSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'caption']
    ordering_fields = ['figure_number', 'created_at']
    ordering = ['figure_number']

    def perform_create(self, serializer):
        # Set the figure number automatically
        document_version = get_object_or_404(DocumentVersion, pk=self.request.data.get('document_version'))
        latest_figure = document_version.figures.order_by('-figure_number').first()
        figure_number = 1
        if latest_figure:
            figure_number = latest_figure.figure_number + 1

        serializer.save(figure_number=figure_number)


class TableViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tables.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'caption']
    ordering_fields = ['table_number', 'created_at']
    ordering = ['table_number']

    def perform_create(self, serializer):
        # Set the table number automatically
        document_version = get_object_or_404(DocumentVersion, pk=self.request.data.get('document_version'))
        latest_table = document_version.tables.order_by('-table_number').first()
        table_number = 1
        if latest_table:
            table_number = latest_table.table_number + 1

        serializer.save(table_number=table_number)


class KeywordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for keywords.
    """
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['keyword']


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for attachments.
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'file_type']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']


class ReviewProcessViewSet(viewsets.ModelViewSet):
    """
    API endpoint for review processes.
    """
    queryset = ReviewProcess.objects.all()
    serializer_class = ReviewProcessSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditorialBoardOrReadOnly]

    def get_queryset(self):
        """
        Filter review processes based on user role:
        - Editorial board members can see all review processes
        - Authors can see review processes for their documents
        - Reviewers can see review processes they're assigned to
        """
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset for schema generation
            return ReviewProcess.objects.none()

        user = self.request.user

        # Editorial board members can see all
        editorial_publications = Publication.objects.filter(editorial_board=user)
        if editorial_publications.exists():
            return ReviewProcess.objects.filter(document_version__publication__in=editorial_publications)

        # Authors can see their own
        authored_documents = DocumentVersion.objects.filter(authors__user=user)

        # Reviewers can see assigned
        reviewer_processes = ReviewProcess.objects.filter(reviewers__user=user)

        return ReviewProcess.objects.filter(
            Q(document_version__in=authored_documents) | 
            Q(id__in=reviewer_processes.values_list('id', flat=True))
        )

    @action(detail=True, methods=['post'])
    def complete_review(self, request, pk=None):
        """
        Complete a review process.
        """
        review_process = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the editorial board member
        if review_process.document_version.publication.editorial_board != request.user:
            return format_error_response('Only editorial board members can complete reviews.', status.HTTP_403_FORBIDDEN)

        # Check if the review is in progress
        if review_process.status != 'in_progress':
            return format_error_response('Only in-progress reviews can be completed.')

        # Update the status
        review_process.status = 'completed'
        review_process.end_date = timezone.now()
        review_process.decision = request.data.get('decision', '')
        review_process.save()

        # Update the document status based on the decision
        document = review_process.document_version
        if request.data.get('accept', False):
            document.status = 'accepted'
        elif request.data.get('revision', False):
            document.status = 'revision'
        else:
            document.status = 'rejected'
            review_process.status = 'rejected'
            review_process.save()

        document.status_date = timezone.now()
        document.status_user = request.user
        document.save()

        serializer = self.get_serializer(review_process)
        return Response(serializer.data)


class ReviewerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for reviewers.
    """
    queryset = Reviewer.objects.all()
    serializer_class = ReviewerSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewerOrReadOnly]

    def get_queryset(self):
        """
        Filter reviewers based on user role:
        - Editorial board members can see all reviewers
        - Reviewers can see only themselves
        """
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return an empty queryset for schema generation
            return Reviewer.objects.none()

        user = self.request.user

        # Editorial board members can see all
        editorial_publications = Publication.objects.filter(editorial_board=user)
        if editorial_publications.exists():
            return Reviewer.objects.filter(
                review_process__document_version__publication__in=editorial_publications
            )

        # Reviewers can see only themselves
        return Reviewer.objects.filter(user=user)

    @action(detail=True, methods=['post'])
    def accept_invitation(self, request, pk=None):
        """
        Accept a review invitation.
        """
        reviewer = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return format_error_response('Only the assigned reviewer can accept the invitation.', status.HTTP_403_FORBIDDEN)

        # Check if the invitation is still pending
        if reviewer.accepted_at is not None:
            return format_error_response('This invitation has already been responded to.')

        # Update the reviewer
        reviewer.accepted_at = timezone.now()
        reviewer.is_active = True
        reviewer.save()

        # Update the review process status if it's the first acceptance
        review_process = reviewer.review_process
        if review_process.status == 'pending':
            review_process.status = 'in_progress'
            review_process.save()

        serializer = self.get_serializer(reviewer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def decline_invitation(self, request, pk=None):
        """
        Decline a review invitation.
        """
        reviewer = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return format_error_response('Only the assigned reviewer can decline the invitation.', status.HTTP_403_FORBIDDEN)

        # Check if the invitation is still pending
        if reviewer.accepted_at is not None:
            return format_error_response('This invitation has already been responded to.')

        # Update the reviewer
        reviewer.is_active = False
        reviewer.save()

        serializer = self.get_serializer(reviewer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_review(self, request, pk=None):
        """
        Mark a review as completed.
        """
        reviewer = self.get_object()

        from core.exceptions import format_error_response

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return format_error_response('Only the assigned reviewer can complete the review.', status.HTTP_403_FORBIDDEN)

        # Check if the reviewer has accepted the invitation
        if not reviewer.accepted_at:
            return format_error_response('You must accept the invitation before completing the review.')

        # Update the reviewer
        reviewer.completed_at = timezone.now()
        reviewer.save()

        serializer = self.get_serializer(reviewer)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def ojs_journals(request):
    """
    Get a list of journals from OJS.

    This endpoint returns a list of journals from the configured OJS instance.

    Returns:
    - 200 OK: Returns the list of journals
    - 400 Bad Request: If there's an error in the OJS API request
    """
    try:
        client = OJSClient()
        journals = client.get_journals()
        return Response(journals)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def ojs_issues(request, journal_id=None):
    """
    Get a list of issues for a journal from OJS.

    This endpoint returns a list of issues for a journal from the configured OJS instance.

    Parameters:
    - journal_id: The ID of the journal (optional, defaults to the configured journal ID)

    Returns:
    - 200 OK: Returns the list of issues
    - 400 Bad Request: If there's an error in the OJS API request
    """
    try:
        client = OJSClient()
        journal_id = journal_id or settings.OJS_JOURNAL_ID
        issues = client.get_issues(journal_id)
        return Response(issues)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def ojs_submissions(request, journal_id=None):
    """
    Get a list of submissions for a journal from OJS.

    This endpoint returns a list of submissions for a journal from the configured OJS instance.

    Parameters:
    - journal_id: The ID of the journal (optional, defaults to the configured journal ID)
    - status: The status of the submissions to retrieve (query parameter)

    Returns:
    - 200 OK: Returns the list of submissions
    - 400 Bad Request: If there's an error in the OJS API request
    """
    try:
        client = OJSClient()
        journal_id = journal_id or settings.OJS_JOURNAL_ID
        status = request.query_params.get('status')
        submissions = client.get_submissions(journal_id, status)
        return Response(submissions)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def ojs_submission(request, submission_id):
    """
    Get a submission from OJS.

    This endpoint returns a submission from the configured OJS instance.

    Parameters:
    - submission_id: The ID of the submission

    Returns:
    - 200 OK: Returns the submission
    - 400 Bad Request: If there's an error in the OJS API request
    """
    try:
        client = OJSClient()
        submission = client.get_submission(submission_id)
        return Response(submission)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def ojs_import_submission(request, submission_id):
    """
    Import a submission from OJS.

    This endpoint imports a submission from the configured OJS instance
    and creates a publication in the system.

    Parameters:
    - submission_id: The ID of the submission

    Returns:
    - 200 OK: Returns the created publication
    - 400 Bad Request: If there's an error in the OJS API request or import process
    """
    try:
        client = OJSClient()
        publication = client.import_submission(submission_id)
        return Response(PublicationSerializer(publication).data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_pdf(request, document_version_id):
    """
    Download a PDF/A document for a document version.

    This endpoint creates a PDF/A document from a document version
    and returns it as a downloadable file.

    Parameters:
    - document_version_id: The ID of the document version
    - include_comments: Whether to include comments in the PDF (query parameter, default: true)

    Returns:
    - 200 OK: Returns the PDF document
    - 400 Bad Request: If there's an error creating the PDF
    - 404 Not Found: If the document version is not found
    """
    from django.http import HttpResponse
    from .archive import ArchiveService

    try:
        document_version = get_object_or_404(DocumentVersion, id=document_version_id)

        # Check if the user has permission to view the document
        if document_version.status != 'published' and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to view this document.'}, status=status.HTTP_403_FORBIDDEN)

        include_comments = request.query_params.get('include_comments', 'true').lower() == 'true'

        # Create the PDF
        pdf_buffer = ArchiveService.create_pdf(document_version, include_comments)

        # Create the response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document_version.publication.title}_v{document_version.version_number}.pdf"'

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def archive_document(request, document_version_id):
    """
    Archive a document version in Reposis.

    This endpoint archives a document version in Reposis.

    Parameters:
    - document_version_id: The ID of the document version
    - include_comments: Whether to include comments in the archived document (query parameter, default: true)

    Returns:
    - 200 OK: Returns the response from Reposis
    - 400 Bad Request: If there's an error archiving the document
    - 404 Not Found: If the document version is not found
    """
    from .archive import ArchiveService

    try:
        document_version = get_object_or_404(DocumentVersion, id=document_version_id)

        include_comments = request.query_params.get('include_comments', 'true').lower() == 'true'

        # Archive the document
        response_data = ArchiveService.archive_in_reposis(document_version, include_comments)

        return Response(response_data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_citation_formats(request):
    """
    Get a list of available citation formats.

    This endpoint returns a list of available citation formats.

    Returns:
    - 200 OK: Returns the list of citation formats
    """
    from .citation import CitationService

    formats = CitationService.get_available_citation_formats()
    return Response(formats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_citation_styles(request):
    """
    Get a list of available citation styles.

    This endpoint returns a list of available citation styles.

    Returns:
    - 200 OK: Returns the list of citation styles
    """
    from .citation import CitationService

    styles = CitationService.get_available_citation_styles()
    return Response(styles)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_citation(request, document_version_id):
    """
    Get a citation for a document version.

    This endpoint returns a citation for a document version in the specified format and style.

    Parameters:
    - document_version_id: The ID of the document version
    - format: The citation format (query parameter, default: bibtex)
    - style: The citation style (query parameter, default: apa)

    Returns:
    - 200 OK: Returns the citation
    - 400 Bad Request: If there's an error generating the citation
    - 404 Not Found: If the document version is not found
    """
    from django.http import HttpResponse
    from .citation import CitationService

    try:
        document_version = get_object_or_404(DocumentVersion, id=document_version_id)

        # Check if the user has permission to view the document
        if document_version.status != 'published' and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to view this document.'}, status=status.HTTP_403_FORBIDDEN)

        format_type = request.query_params.get('format', 'bibtex')
        citation_style = request.query_params.get('style', 'apa')

        # Get the citation
        citation = CitationService.generate_citation(document_version, format_type, citation_style)

        # Get the file extension
        formats = CitationService.get_available_citation_formats()
        extension = next((f['extension'] for f in formats if f['id'] == format_type), 'txt')

        # Create the response
        response = HttpResponse(citation, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{document_version.publication.title}_v{document_version.version_number}.{extension}"'

        return response

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_publications(request):
    """
    Get a list of public publications.

    This endpoint returns a list of published publications for public consumption.

    Parameters:
    - section: The section to filter by (query parameter)
    - limit: The maximum number of publications to return (query parameter, default: 10)

    Returns:
    - 200 OK: Returns the list of publications
    """
    # Get the query parameters
    section = request.query_params.get('section')
    limit = int(request.query_params.get('limit', 10))

    # Get the publications
    publications = Publication.objects.filter(
        document_versions__status='published'
    ).distinct()

    # Apply filters
    if section:
        publications = publications.filter(section=section)

    # Limit the number of publications
    publications = publications[:limit]

    # Serialize the publications
    serializer = PublicationListSerializer(publications, many=True)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_document_version(request, document_version_id):
    """
    Get a public document version.

    This endpoint returns a published document version for public consumption.

    Parameters:
    - document_version_id: The ID of the document version

    Returns:
    - 200 OK: Returns the document version
    - 404 Not Found: If the document version is not found or not published
    """
    try:
        # Get the document version
        document_version = get_object_or_404(
            DocumentVersion,
            id=document_version_id,
            status='published'
        )

        # Serialize the document version
        serializer = DocumentVersionSerializer(document_version)

        return Response(serializer.data)

    except DocumentVersion.DoesNotExist:
        from core.exceptions import format_error_response
        return format_error_response('Document version not found or not published.', status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_jats(request, document_version_id):
    """
    Export a document version to JATS-XML format.

    This endpoint exports a document version to JATS-XML format for submission to repositories.

    Parameters:
    - document_version_id: The ID of the document version

    Returns:
    - 200 OK: Returns the JATS-XML document
    - 400 Bad Request: If there's an error creating the JATS-XML
    - 404 Not Found: If the document version is not found
    """
    from django.http import HttpResponse
    from .jats_converter import JATSConverter

    try:
        document_version = get_object_or_404(DocumentVersion, id=document_version_id)

        # Check if the user has permission to view the document
        if document_version.status != 'published' and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to view this document.'}, status=status.HTTP_403_FORBIDDEN)

        # Generate JATS-XML
        jats_xml = JATSConverter.document_to_jats(document_version)

        # Create the response
        response = HttpResponse(jats_xml, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{document_version.publication.title}_v{document_version.version_number}.xml"'

        return response

    except Exception as e:
        logger.error(f"Error exporting to JATS-XML: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_to_repository(request, document_version_id):
    """
    Export a document version to a repository.

    This endpoint exports a document version to a specified repository (PubMed Central, Europe PMC, etc.)
    using JATS-XML format.

    Parameters:
    - document_version_id: The ID of the document version
    - repository: The repository to export to (query parameter, options: 'pubmed', 'europepmc', 'institutional')

    Returns:
    - 200 OK: Returns a success message with any repository-specific information
    - 400 Bad Request: If there's an error exporting to the repository
    - 404 Not Found: If the document version is not found
    """
    from .jats_converter import JATSConverter

    try:
        document_version = get_object_or_404(DocumentVersion, id=document_version_id)

        # Check if the user has permission to view the document
        if document_version.status != 'published' and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to view this document.'}, status=status.HTTP_403_FORBIDDEN)

        # Get the repository
        repository = request.query_params.get('repository', '').lower()
        if not repository:
            return Response({'error': 'Repository parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JATS-XML
        jats_xml = JATSConverter.document_to_jats(document_version)

        # Export to the specified repository
        # Note: This is a placeholder for actual repository submission logic
        # In a real implementation, you would use repository-specific APIs to submit the JATS-XML

        response_data = {
            'status': 'success',
            'message': f'Document successfully exported to {repository}',
            'repository': repository,
            'document_title': document_version.publication.title,
            'document_version': document_version.version_number,
            'doi': document_version.doi
        }

        # Add repository-specific information
        if repository == 'pubmed':
            response_data['repository_name'] = 'PubMed Central'
            response_data['repository_url'] = 'https://www.ncbi.nlm.nih.gov/pmc/'
        elif repository == 'europepmc':
            response_data['repository_name'] = 'Europe PMC'
            response_data['repository_url'] = 'https://europepmc.org/'
        elif repository == 'institutional':
            response_data['repository_name'] = 'Institutional Repository'
            # This would be configured based on the institution
            response_data['repository_url'] = 'https://repository.institution.edu/'
        else:
            return Response({'error': f'Unsupported repository: {repository}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error exporting to repository: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_comments(request, document_version_id=None):
    """
    Get a list of public comments.

    This endpoint returns a list of published comments for public consumption.
    Comments are only returned for document versions with open discussions.

    Parameters:
    - document_version_id: The ID of the document version (optional)
    - section: The section to filter by (query parameter)
    - limit: The maximum number of comments to return (query parameter, default: 10)
    - include_closed: Whether to include comments from closed discussions (query parameter, default: false)

    Returns:
    - 200 OK: Returns the list of comments
    """
    from comments.models import Comment
    from comments.serializers import CommentSerializer

    # Get the query parameters
    section = request.query_params.get('section')
    limit = int(request.query_params.get('limit', 10))
    include_closed = request.query_params.get('include_closed', 'false').lower() == 'true'

    # Get the comments
    comments = Comment.objects.filter(status='published')

    # Apply filters
    if document_version_id:
        comments = comments.filter(document_version_id=document_version_id)

        # Check if the document version exists and if discussions are open
        try:
            document_version = DocumentVersion.objects.get(id=document_version_id)
            if document_version.discussion_status != 'open' and not include_closed:
                # If discussions are closed and include_closed is false, return empty list
                return Response([])
        except DocumentVersion.DoesNotExist:
            # If document version doesn't exist, return 404
            return Response({'error': 'Document version not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Only include comments from document versions with open discussions
        if not include_closed:
            comments = comments.filter(document_version__discussion_status='open')

    if section:
        comments = comments.filter(document_version__publication__section=section)

    # Limit the number of comments
    comments = comments[:limit]

    # Serialize the comments
    serializer = CommentSerializer(comments, many=True)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_document(request, document_version_id=None):
    """
    Import a document file (Word, LaTeX, PDF) and convert it to JATS-XML.

    This endpoint imports a document file, extracts its content and metadata,
    and converts it to JATS-XML format. If a document_version_id is provided,
    the document version will be updated with the extracted content.

    Parameters:
    - document_version_id: The ID of the document version to update (optional)
    - file: The document file to import (multipart/form-data)

    Returns:
    - 200 OK: Returns the extracted content and metadata
    - 400 Bad Request: If there's an error importing the document
    - 404 Not Found: If the document version is not found
    """
    try:
        # Check if a file was uploaded
        if 'file' not in request.FILES:
            return Response({'error': 'No file was uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES['file']
        file_name = file_obj.name

        # Check if the file extension is supported
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in ['.docx', '.doc', '.pdf', '.tex', '.latex']:
            return Response(
                {'error': f'Unsupported file format: {file_ext}. Supported formats are: .docx, .doc, .pdf, .tex, .latex'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the document version if provided
        document_version = None
        if document_version_id:
            document_version = get_object_or_404(DocumentVersion, id=document_version_id)

            # Check if the user has permission to update the document version
            if document_version.status != 'draft' and not request.user.is_staff:
                return Response(
                    {'error': 'You do not have permission to update this document version.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Import the document
        content = ImportService.import_document(file_obj, file_name, document_version)

        # If a document version was provided, update it with the extracted content
        if document_version:
            # Update the document version with the extracted content
            document_version.title = content.get('title', document_version.title)
            document_version.abstract = content.get('abstract', document_version.abstract)

            # Store the JATS-XML content and convert to HTML for display
            jats_xml = content.get('jats_xml', '')
            if jats_xml:
                # Convert JATS-XML to HTML and store in content field
                html_content = JATSConverter.jats_to_html(jats_xml)
                document_version.content = html_content

            # Update the document version's metadata
            if content.get('doi'):
                document_version.publication.meta_doi = content.get('doi')
                document_version.publication.save(update_fields=['meta_doi'])

            # Save the document version
            document_version.save(update_fields=['title', 'abstract', 'content'])

            # Create authors if they don't exist
            for author_name in content.get('authors', []):
                # Check if the author already exists
                if not Author.objects.filter(document_version=document_version, name=author_name).exists():
                    Author.objects.create(
                        document_version=document_version,
                        name=author_name,
                        user=request.user if request.user.get_full_name() == author_name else None
                    )

            # Return the updated document version
            return Response(DocumentVersionSerializer(document_version).data)

        # If no document version was provided, just return the extracted content
        return Response(content)

    except Exception as e:
        logger.error(f"Error importing document: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
