from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from publications.models import Publication, DocumentVersion
from comments.models import Comment

User = get_user_model()


class AnalyticsService:
    """
    Service for generating analytics data.
    
    This service provides methods for:
    - Counting users, documents, and comments
    - Tracking document views
    - Generating analytics reports
    """
    
    @staticmethod
    def get_user_count(time_period=None):
        """
        Get the number of registered users.
        
        Args:
            time_period (str, optional): The time period to filter by
                                       ('day', 'week', 'month', 'year', 'all')
            
        Returns:
            int: The number of users
        """
        users = User.objects.all()
        
        if time_period:
            now = timezone.now()
            
            if time_period == 'day':
                users = users.filter(date_joined__gte=now - timezone.timedelta(days=1))
            elif time_period == 'week':
                users = users.filter(date_joined__gte=now - timezone.timedelta(weeks=1))
            elif time_period == 'month':
                users = users.filter(date_joined__gte=now - timezone.timedelta(days=30))
            elif time_period == 'year':
                users = users.filter(date_joined__gte=now - timezone.timedelta(days=365))
        
        return users.count()
    
    @staticmethod
    def get_document_count(time_period=None, status=None):
        """
        Get the number of documents.
        
        Args:
            time_period (str, optional): The time period to filter by
                                       ('day', 'week', 'month', 'year', 'all')
            status (str, optional): The status to filter by
                                  ('draft', 'published', etc.)
            
        Returns:
            int: The number of documents
        """
        documents = DocumentVersion.objects.all()
        
        if status:
            documents = documents.filter(status=status)
        
        if time_period:
            now = timezone.now()
            
            if time_period == 'day':
                documents = documents.filter(created_at__gte=now - timezone.timedelta(days=1))
            elif time_period == 'week':
                documents = documents.filter(created_at__gte=now - timezone.timedelta(weeks=1))
            elif time_period == 'month':
                documents = documents.filter(created_at__gte=now - timezone.timedelta(days=30))
            elif time_period == 'year':
                documents = documents.filter(created_at__gte=now - timezone.timedelta(days=365))
        
        return documents.count()
    
    @staticmethod
    def get_comment_count(time_period=None, status=None, comment_type=None):
        """
        Get the number of comments.
        
        Args:
            time_period (str, optional): The time period to filter by
                                       ('day', 'week', 'month', 'year', 'all')
            status (str, optional): The status to filter by
                                  ('draft', 'published', etc.)
            comment_type (str, optional): The comment type to filter by
                                        ('SC', 'rSC', 'ER', 'AD', 'NP')
            
        Returns:
            int: The number of comments
        """
        comments = Comment.objects.all()
        
        if status:
            comments = comments.filter(status=status)
        
        if comment_type:
            comments = comments.filter(comment_type__code=comment_type)
        
        if time_period:
            now = timezone.now()
            
            if time_period == 'day':
                comments = comments.filter(created_at__gte=now - timezone.timedelta(days=1))
            elif time_period == 'week':
                comments = comments.filter(created_at__gte=now - timezone.timedelta(weeks=1))
            elif time_period == 'month':
                comments = comments.filter(created_at__gte=now - timezone.timedelta(days=30))
            elif time_period == 'year':
                comments = comments.filter(created_at__gte=now - timezone.timedelta(days=365))
        
        return comments.count()
    
    @staticmethod
    def get_document_views(document_version_id=None, time_period=None):
        """
        Get the number of document views.
        
        Args:
            document_version_id (int, optional): The ID of the document version
            time_period (str, optional): The time period to filter by
                                       ('day', 'week', 'month', 'year', 'all')
            
        Returns:
            int: The number of document views
        """
        # In a real implementation, this would query a view tracking table
        # For now, we'll return a dummy value
        return 42
    
    @staticmethod
    def get_analytics_summary():
        """
        Get a summary of analytics data.
        
        Returns:
            dict: A summary of analytics data
        """
        return {
            'users': {
                'total': AnalyticsService.get_user_count(),
                'day': AnalyticsService.get_user_count('day'),
                'week': AnalyticsService.get_user_count('week'),
                'month': AnalyticsService.get_user_count('month'),
                'year': AnalyticsService.get_user_count('year'),
            },
            'documents': {
                'total': AnalyticsService.get_document_count(),
                'published': AnalyticsService.get_document_count(status='published'),
                'day': AnalyticsService.get_document_count('day'),
                'week': AnalyticsService.get_document_count('week'),
                'month': AnalyticsService.get_document_count('month'),
                'year': AnalyticsService.get_document_count('year'),
            },
            'comments': {
                'total': AnalyticsService.get_comment_count(),
                'published': AnalyticsService.get_comment_count(status='published'),
                'day': AnalyticsService.get_comment_count('day'),
                'week': AnalyticsService.get_comment_count('week'),
                'month': AnalyticsService.get_comment_count('month'),
                'year': AnalyticsService.get_comment_count('year'),
                'by_type': {
                    'SC': AnalyticsService.get_comment_count(comment_type='SC'),
                    'rSC': AnalyticsService.get_comment_count(comment_type='rSC'),
                    'ER': AnalyticsService.get_comment_count(comment_type='ER'),
                    'AD': AnalyticsService.get_comment_count(comment_type='AD'),
                    'NP': AnalyticsService.get_comment_count(comment_type='NP'),
                },
            },
        }