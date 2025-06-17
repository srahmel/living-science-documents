from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from publications.models import Publication, DocumentVersion, Author
from comments.models import CommentType, Comment
import json

User = get_user_model()

class ScientificCommentTest(TestCase):
    """Test creating a comment with 'scientific' as the comment_type"""

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create a publication
        self.publication = Publication.objects.create(
            title='Test Publication',
            status='published',
            editorial_board=self.user
        )

        # Create a document version
        self.version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=5,
            status='published',
            doi='10.1234/test.2023.001.v1',
            content='Test content'
        )

        # Create an author for the document version
        Author.objects.create(
            document_version=self.version,
            user=self.user,
            name='Test User',
            email='test@example.com',
            is_corresponding=True
        )

        # Create comment types if they don't exist
        for code, name in [
            ('SC', 'Scientific Comment'),
            ('rSC', 'Response to Scientific Comment'),
            ('ER', 'Error Correction'),
            ('AD', 'Additional Data'),
            ('NP', 'New Publication')
        ]:
            CommentType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': f'Description for {name}',
                    'requires_doi': code != 'ER'
                }
            )

        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # URL for creating comments
        self.comments_url = reverse('comment-list')

    def test_create_scientific_comment(self):
        """Test creating a comment with 'scientific' as the comment_type"""
        # This is based on the payload from the issue description
        comment_data = {
            "document_version": self.version.id,
            "content": "Das ist so alt, das wurde schon für klassische Drucksachen genutzt. Wer hat es wohl erfunden?",
            "comment_type": "scientific",
            "line_number": 5,
            "text_selection": "Lorem ipsum dolor sit amet",
            "doi_requested": False
        }

        response = self.client.post(self.comments_url, comment_data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.comment_type.code, 'SC')