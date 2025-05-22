from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import Publication, DocumentVersion, Author, Figure, Table, Keyword, Attachment, ReviewProcess, Reviewer
from .serializers import (
    PublicationSerializer, PublicationListSerializer, 
    DocumentVersionSerializer, DocumentVersionListSerializer,
    AuthorSerializer, FigureSerializer, TableSerializer, 
    KeywordSerializer, AttachmentSerializer,
    ReviewProcessSerializer, ReviewerSerializer
)
from .ojs import OJSClient


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
        serializer.save(editorial_board=self.request.user)

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
        """
        publication = self.get_object()
        version = publication.current_version()
        if version:
            serializer = DocumentVersionSerializer(version)
            return Response(serializer.data)
        return Response({'detail': 'No published version found.'}, status=status.HTTP_404_NOT_FOUND)


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

    def perform_create(self, serializer):
        # Set the version number automatically
        publication = get_object_or_404(Publication, pk=self.request.data.get('publication'))
        latest_version = publication.document_versions.order_by('-version_number').first()
        version_number = 1
        if latest_version:
            version_number = latest_version.version_number + 1

        serializer.save(
            version_number=version_number,
            status_user=self.request.user,
            status_date=timezone.now()
        )

    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """
        Submit a document version for review.
        """
        document = self.get_object()

        # Check if the user is an author
        if not document.authors.filter(user=request.user).exists():
            return Response({'detail': 'Only authors can submit for review.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the document is in draft status
        if document.status != 'draft':
            return Response({'detail': 'Only draft documents can be submitted for review.'}, status=status.HTTP_400_BAD_REQUEST)

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
    def publish(self, request, pk=None):
        """
        Publish a document version.
        """
        document = self.get_object()

        # Check if the user is the editorial board member
        if document.publication.editorial_board != request.user:
            return Response({'detail': 'Only editorial board members can publish documents.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the document is in accepted status
        if document.status != 'accepted':
            return Response({'detail': 'Only accepted documents can be published.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the status
        document.status = 'published'
        document.status_date = timezone.now()
        document.status_user = request.user
        document.release_date = timezone.now().date()
        document.save()

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

        # Check if the user is the editorial board member
        if review_process.document_version.publication.editorial_board != request.user:
            return Response({'detail': 'Only editorial board members can complete reviews.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the review is in progress
        if review_process.status != 'in_progress':
            return Response({'detail': 'Only in-progress reviews can be completed.'}, status=status.HTTP_400_BAD_REQUEST)

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

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return Response({'detail': 'Only the assigned reviewer can accept the invitation.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the invitation is still pending
        if reviewer.accepted_at is not None:
            return Response({'detail': 'This invitation has already been responded to.'}, status=status.HTTP_400_BAD_REQUEST)

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

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return Response({'detail': 'Only the assigned reviewer can decline the invitation.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the invitation is still pending
        if reviewer.accepted_at is not None:
            return Response({'detail': 'This invitation has already been responded to.'}, status=status.HTTP_400_BAD_REQUEST)

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

        # Check if the user is the reviewer
        if reviewer.user != request.user:
            return Response({'detail': 'Only the assigned reviewer can complete the review.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the reviewer has accepted the invitation
        if not reviewer.accepted_at:
            return Response({'detail': 'You must accept the invitation before completing the review.'}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response(
            {'detail': 'Document version not found or not published.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def public_comments(request, document_version_id=None):
    """
    Get a list of public comments.

    This endpoint returns a list of published comments for public consumption.

    Parameters:
    - document_version_id: The ID of the document version (optional)
    - section: The section to filter by (query parameter)
    - limit: The maximum number of comments to return (query parameter, default: 10)

    Returns:
    - 200 OK: Returns the list of comments
    """
    from comments.models import Comment
    from comments.serializers import CommentSerializer

    # Get the query parameters
    section = request.query_params.get('section')
    limit = int(request.query_params.get('limit', 10))

    # Get the comments
    comments = Comment.objects.filter(status='published')

    # Apply filters
    if document_version_id:
        comments = comments.filter(document_version_id=document_version_id)

    if section:
        comments = comments.filter(document_version__publication__section=section)

    # Limit the number of comments
    comments = comments[:limit]

    # Serialize the comments
    serializer = CommentSerializer(comments, many=True)

    return Response(serializer.data)
