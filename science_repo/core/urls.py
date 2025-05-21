from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/orcid/login/', views.orcid_login, name='orcid_login'),
    path('auth/orcid/callback/', views.orcid_callback, name='orcid_callback'),
]