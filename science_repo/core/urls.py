
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
    path('orcid/login/', views.orcid_login, name='orcid_login'),
    path('orcid/callback/', views.orcid_callback, name='orcid_callback'),
    path('', include(router.urls)),
    # Analytics endpoints
    path('analytics/summary/', views.analytics_summary, name='analytics-summary'),
    path('analytics/users/', views.analytics_users, name='analytics-users'),
    path('analytics/documents/', views.analytics_documents, name='analytics-documents'),
    path('analytics/comments/', views.analytics_comments, name='analytics-comments'),
    path('analytics/document-views/', views.analytics_document_views, name='analytics-document-views'),
    path('analytics/document-views/<int:document_version_id>/', views.analytics_document_views, name='analytics-document-views-by-id'),
]