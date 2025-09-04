from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from core import views as core_views

# Get the base URL from settings
base_url = settings.FORCE_SCRIPT_NAME or ''

schema_view = get_schema_view(
    openapi.Info(
        title="Living Science Documents API",
        default_version='v1',
        description="API documentation for the Living Science Documents platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url=f"{settings.API_BASE_URL}{settings.API_PATH}",
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/publications/', include('publications.urls')),
    path('api/comments/', include('comments.urls')),
    path('api/ai/', include('ai_assistant.urls')),
    # Frontend helper pages (not under /api)
    re_path(r'^login/success/?$', core_views.login_success_page, name='login-success'),
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # Use a custom Swagger UI template to fix button contrast issues
    path('swagger/', include('science_repo.swagger_ui')),  # delegates to a small module with TemplateView
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
