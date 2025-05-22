from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'publications', views.PublicationViewSet)
router.register(r'document-versions', views.DocumentVersionViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'figures', views.FigureViewSet)
router.register(r'tables', views.TableViewSet)
router.register(r'keywords', views.KeywordViewSet)
router.register(r'attachments', views.AttachmentViewSet)
router.register(r'review-processes', views.ReviewProcessViewSet)
router.register(r'reviewers', views.ReviewerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # OJS endpoints
    path('ojs/journals/', views.ojs_journals, name='ojs-journals'),
    path('ojs/issues/', views.ojs_issues, name='ojs-issues'),
    path('ojs/issues/<int:journal_id>/', views.ojs_issues, name='ojs-issues-by-journal'),
    path('ojs/submissions/', views.ojs_submissions, name='ojs-submissions'),
    path('ojs/submissions/<int:journal_id>/', views.ojs_submissions, name='ojs-submissions-by-journal'),
    path('ojs/submission/<int:submission_id>/', views.ojs_submission, name='ojs-submission'),
    path('ojs/import/<int:submission_id>/', views.ojs_import_submission, name='ojs-import-submission'),
    # Archive endpoints
    path('document-versions/<int:document_version_id>/pdf/', views.download_pdf, name='download-pdf'),
    path('document-versions/<int:document_version_id>/archive/', views.archive_document, name='archive-document'),
    # Citation endpoints
    path('citation/formats/', views.get_citation_formats, name='citation-formats'),
    path('citation/styles/', views.get_citation_styles, name='citation-styles'),
    path('document-versions/<int:document_version_id>/citation/', views.get_citation, name='get-citation'),
    # Public API endpoints
    path('public/publications/', views.public_publications, name='public-publications'),
    path('public/document-versions/<int:document_version_id>/', views.public_document_version, name='public-document-version'),
    path('public/comments/', views.public_comments, name='public-comments'),
    path('public/comments/<int:document_version_id>/', views.public_comments, name='public-comments-by-document'),
]
