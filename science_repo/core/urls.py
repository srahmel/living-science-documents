
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Use the new public CSRF token view that explicitly bypasses authentication
    path('csrf/', views.PublicCSRFTokenView.as_view(), name='csrf_token'),
    path('logout/', views.logout_view, name='logout'),
    path('roles/', views.RoleManagementView.as_view(), name='role-management'),
    path('orcid/login/', views.orcid_login, name='orcid_login'),
    path('audits/', views.AuditLogListView.as_view(), name='audit-list'),
    path('orcid/callback/', views.orcid_callback, name='orcid_callback'),
    # Password reset endpoints
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    path('', include(router.urls)),
    # Analytics endpoints
    path('analytics/summary/', views.analytics_summary, name='analytics-summary'),
    path('analytics/users/', views.analytics_users, name='analytics-users'),
    path('analytics/documents/', views.analytics_documents, name='analytics-documents'),
    path('analytics/comments/', views.analytics_comments, name='analytics-comments'),
    path('analytics/document-views/', views.analytics_document_views, name='analytics-document-views'),
    path('analytics/document-views/<int:document_version_id>/', views.analytics_document_views, name='analytics-document-views-by-id'),
]
