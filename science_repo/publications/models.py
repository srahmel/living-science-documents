from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Publication(models.Model):
    """
    Publication model representing a scientific publication.
    A publication can have multiple document versions.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('revision', 'Revision'),
        ('accepted', 'Accepted'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    meta_doi = models.CharField(max_length=200, unique=True, null=True, blank=True)
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    editorial_board = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_publications')

    def __str__(self):
        return self.title

    def current_version(self):
        """Returns the latest published version of this publication"""
        return self.document_versions.filter(status='published').order_by('-version_number').first()

    def latest_version(self):
        """Returns the latest version of this publication regardless of status"""
        return self.document_versions.order_by('-version_number').first()


class DocumentVersion(models.Model):
    """
    DocumentVersion model representing a specific version of a publication.
    Each version has its own DOI and can be cited independently.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('revision', 'Revision'),
        ('accepted', 'Accepted'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='document_versions')
    version_number = models.PositiveIntegerField()
    doi = models.CharField(max_length=200, unique=True)
    content = models.TextField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True, help_text="HTML version of the content for display")
    original_file = models.CharField(max_length=500, blank=True, null=True, help_text="Path to the original imported file")
    technical_abstract = models.TextField(blank=True, null=True)
    non_technical_abstract = models.TextField(blank=True, null=True)
    introduction = models.TextField(blank=True, null=True)
    methodology = models.TextField(blank=True, null=True)
    main_text = models.TextField(blank=True, null=True)
    conclusion = models.TextField(blank=True, null=True)
    author_contributions = models.TextField(blank=True, null=True)
    conflicts_of_interest = models.TextField(blank=True, null=True)
    acknowledgments = models.TextField(blank=True, null=True)
    funding = models.TextField(blank=True, null=True)
    references = models.TextField(blank=True, null=True)
    reviewer_response = models.TextField(blank=True, null=True, help_text="Response to reviewer/editor recommendations for revised submissions")
    metadata = models.JSONField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    status_date = models.DateTimeField(default=timezone.now)
    status_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="status_document_versions")

    class Meta:
        unique_together = ('publication', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.publication.title} v{self.version_number}"


class Author(models.Model):
    """
    Author model representing an author of a document version.
    An author can be linked to a user account but doesn't have to be.
    """
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='authors')
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    institution = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    orcid = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="publication_authors")
    order = models.PositiveIntegerField(default=0)
    is_corresponding = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Figure(models.Model):
    """
    Figure model representing a figure in a document version.
    """
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='figures')
    figure_number = models.PositiveIntegerField()
    title = models.CharField(max_length=500)
    caption = models.TextField()
    image = models.ImageField(upload_to='figures/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('document_version', 'figure_number')
        ordering = ['figure_number']

    def __str__(self):
        return f"Figure {self.figure_number}: {self.title}"


class Table(models.Model):
    """
    Table model representing a table in a document version.
    """
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='tables')
    table_number = models.PositiveIntegerField()
    title = models.CharField(max_length=500)
    caption = models.TextField()
    content = models.TextField()  # HTML or Markdown representation of the table
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('document_version', 'table_number')
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number}: {self.title}"


class Keyword(models.Model):
    """
    Keyword model representing a keyword for a document version.
    """
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=100)

    class Meta:
        unique_together = ('document_version', 'keyword')

    def __str__(self):
        return self.keyword


class Attachment(models.Model):
    """
    Attachment model representing additional files attached to a document version.
    """
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='attachments/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ReviewProcess(models.Model):
    """
    ReviewProcess model representing the review process for a document version.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    document_version = models.OneToOneField(DocumentVersion, on_delete=models.CASCADE, related_name='review_process')
    handling_editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='handled_reviews')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decision = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Review of {self.document_version}"


class Reviewer(models.Model):
    """
    Reviewer model representing a reviewer assigned to a review process.
    """
    review_process = models.ForeignKey(ReviewProcess, on_delete=models.CASCADE, related_name='reviewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_assignments')
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} reviewing {self.review_process.document_version}"
