from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'comment-types', views.CommentTypeViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'comment-authors', views.CommentAuthorViewSet)
router.register(r'comment-references', views.CommentReferenceViewSet)
router.register(r'conflicts-of-interest', views.ConflictOfInterestViewSet)
router.register(r'comment-moderations', views.CommentModerationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]