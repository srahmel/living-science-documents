from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from publications.models import DocumentVersion

User = get_user_model()

class CommentChat(models.Model):
    """
    CommentChat model representing a chat thread for a comment.
    Each comment can have one chat thread.
    """
    comment = models.OneToOneField('Comment', on_delete=models.CASCADE, related_name='chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat for {self.comment}"


class ChatMessage(models.Model):
    """
    ChatMessage model representing a message in a comment chat.
    """
    chat = models.ForeignKey(CommentChat, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.user.get_full_name()} in {self.chat}"


class CommentType(models.Model):
    """
    CommentType model representing the type of comment.
    Types include SC (Scientific Comment), rSC (Response to Scientific Comment),
    ER (Error Correction), AD (Additional Data), NP (New Publication).
    """
    class CodeChoices(models.TextChoices):
        SCIENTIFIC_COMMENT = 'SC', 'Scientific Comment'
        RESPONSE_TO_SC = 'rSC', 'Response to Scientific Comment'
        ERROR_CORRECTION = 'ER', 'Error Correction'
        ADDITIONAL_DATA = 'AD', 'Additional Data'
        NEW_PUBLICATION = 'NP', 'New Publication'

    code = models.CharField(max_length=10, unique=True, choices=CodeChoices.choices)
    name = models.CharField(max_length=100)
    description = models.TextField()
    requires_doi = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Comment(models.Model):
    """
    Comment model representing a comment on a document version.
    Comments can be linked to specific sections or lines of the document.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    document_version = models.ForeignKey(DocumentVersion, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='responses')
    comment_type = models.ForeignKey(CommentType, on_delete=models.PROTECT, related_name='comments')
    content = models.TextField()
    referenced_text = models.TextField(null=True, blank=True)
    section_reference = models.CharField(max_length=100, null=True, blank=True)
    line_start = models.PositiveIntegerField(null=True, blank=True)
    line_end = models.PositiveIntegerField(null=True, blank=True)
    range_hash = models.CharField(max_length=100, null=True, blank=True)
    doi = models.CharField(max_length=200, null=True, blank=True, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_date = models.DateTimeField(default=timezone.now)
    status_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="moderated_comments")
    is_ai_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.comment_type.code} on {self.document_version} by {self.authors.first() if self.authors.exists() else 'Unknown'}"

    def is_question(self):
        """Check if the comment is in question form as required by guidelines"""
        return self.content.strip().endswith('?')


class CommentAuthor(models.Model):
    """
    CommentAuthor model representing an author of a comment.
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='authors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_comments')
    is_corresponding = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user.get_full_name()} on {self.comment}"


class CommentReference(models.Model):
    """
    CommentReference model representing a reference cited in a comment.
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='references')
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    publication_date = models.DateField(null=True, blank=True)
    doi = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    citation_text = models.TextField()
    trust_level = models.CharField(max_length=20, choices=[
        ('high', 'High - Peer Reviewed'),
        ('medium', 'Medium - Verified Comment'),
        ('low', 'Low - External Source'),
    ])

    def __str__(self):
        return self.title


class ConflictOfInterest(models.Model):
    """
    ConflictOfInterest model representing a conflict of interest declaration for a comment.
    """
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE, related_name='conflict_of_interest')
    statement = models.TextField(default="None")
    has_conflict = models.BooleanField(default=False)

    def __str__(self):
        return f"COI for {self.comment}"


class CommentModeration(models.Model):
    """
    CommentModeration model representing the moderation process for a comment.
    Includes a simple checklist for validation steps.
    """
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE, related_name='moderation')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderated')
    moderation_date = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ])
    decision_reason = models.TextField(null=True, blank=True)
    checked_question_form = models.BooleanField(default=False)
    checked_sources = models.BooleanField(default=False)
    checked_anchor = models.BooleanField(default=False)

    def __str__(self):
        return f"Moderation of {self.comment} by {self.moderator.get_full_name()}"
