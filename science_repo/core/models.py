# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


# 🧑 Benutzerprofil mit ORCID
class User(AbstractUser):
    orcid = models.CharField(max_length=50, unique=True, null=True, blank=True)
    affiliation = models.CharField(max_length=255, null=True, blank=True)
    research_field = models.CharField(max_length=255, null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    external_link = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    dsgvo_consent = models.BooleanField(default=False)
    license_consent = models.BooleanField(default=False)
    notification_consent = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username


# 📚 Publikation (übergreifende Klammer)
class Publication(models.Model):
    meta_doi = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


# 📄 Dokument (eine Version)
class Document(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='documents')
    doi = models.CharField(max_length=200, unique=True)
    metadata = models.JSONField(null=True, blank=True)
    content = models.TextField()
    release_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50)  # To be mapped to status list
    status_date = models.DateField()
    status_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="status_documents")


# 🧑‍🎓 Autor (auch ohne User-Zuordnung möglich)
class Author(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='authors')
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    institution = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    orcid = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="core_authors")


# 💬 Kommentar
class Comment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    referenced_text = models.TextField(null=True, blank=True)
    content = models.TextField()
    comment_type = models.CharField(max_length=10)  # ER, SC, rSC, NP
    status = models.CharField(max_length=50)  # draft, submitted, published, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    status_date = models.DateField()
    status_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="core_moderated_comments")
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_comments")
    doi = models.CharField(max_length=200, null=True, blank=True)


# 👥 Kommentatoren
class CommentAuthor(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='authors')
    user = models.ForeignKey(User, on_delete=models.CASCADE)


# ❗ Interessenkonflikte
class ConflictOfInterest(models.Model):
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    statement = models.TextField(default="None")


# 🔠 Kommentartypen (Lookup)
class CommentType(models.Model):
    short_code = models.CharField(max_length=10, unique=True)  # ER, SC, etc.
    description = models.CharField(max_length=255)


# 🔍 Erweiterte Suche (gespeichert)
class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# 🔍 Suchattribut (Lookup)
class SearchAttribute(models.Model):
    attribute = models.CharField(max_length=100)
    operator = models.CharField(max_length=20)
    value = models.CharField(max_length=255)
    search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name='filters')


# 🧑 Alias-Namen
class UserAlias(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)


# 🏷️ Stichworte
class Keyword(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='keywords')
    keyword = models.CharField(max_length=100, unique=True)
