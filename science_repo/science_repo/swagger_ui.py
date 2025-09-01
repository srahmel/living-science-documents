from django.urls import path
from django.views.generic import TemplateView

app_name = 'swagger_ui_custom'

urlpatterns = [
    path('', TemplateView.as_view(template_name='swagger-ui-custom.html'), name='schema-swagger-ui'),
]
