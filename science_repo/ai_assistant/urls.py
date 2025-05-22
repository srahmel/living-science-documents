from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ai-models', views.AIModelViewSet)
router.register(r'ai-prompts', views.AIPromptViewSet)
router.register(r'ai-comment-suggestions', views.AICommentSuggestionViewSet)
router.register(r'ai-prompt-logs', views.AIPromptLogViewSet)
router.register(r'ai-references', views.AIReferenceViewSet)
router.register(r'ai-feedback', views.AIFeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
]