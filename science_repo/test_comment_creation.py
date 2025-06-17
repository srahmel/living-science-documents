from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from publications.models import Publication, DocumentVersion, Author
from comments.models import CommentType, Comment
import json

User = get_user_model()

class CommentCreationTest(TestCase):
    """Test creating comments with string comment_type"""

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
            version_number=1,
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
        CommentType.objects.get_or_create(
            code='ER',
            defaults={
                'name': 'Error Correction',
                'description': 'Correction of errors',
                'requires_doi': False
            }
        )

        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # URL for creating comments
        self.comments_url = reverse('comment-list')

    def test_create_comment_with_string_type(self):
        """Test creating a comment with a string comment_type"""
        # Test with 'error' which should map to 'ER'
        comment_data = {
            'document_version': self.version.id,
            'content': 'Wird ja vor allem bei Grafik Designern im Print-Layout verwendet?',
            'comment_type': 'error',
            'line_number': 5,
            'text_selection': 'Wer Webseiten, Layouts oder Publikationen gestaltet, stößt auf einen alten Bekannten: „Lorem ipsum dolor sit amet..." – der Dummy-Text, der aussieht wie Latein, sich aber irgendwie falsch anfühlt. Woran liegt das? Was unterscheidet diesen scheinbar römischen Wortsalat von echtem Latein, wie es Cicero geschrieben hat? Sind die Unterschiede nur oberflächlich oder steckt mehr dahinter?',
            'doi_requested': False
        }

        response = self.client.post(self.comments_url, comment_data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.comment_type.code, 'ER')

        # Clean up
        Comment.objects.all().delete()

    def test_create_comment_with_various_string_types(self):
        """Test creating comments with various string representations of comment types"""
        # Create all comment types if they don't exist
        for code, name in [
            ('SC', 'Scientific Comment'),
            ('rSC', 'Response to Scientific Comment'),
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

        # Test various string representations
        test_cases = [
            ('scientific', 'SC'),
            ('Scientific Comment', 'SC'),
            ('SCIENTIFIC_COMMENT', 'SC'),
            ('response', 'rSC'),
            ('Response to SC', 'rSC'),
            ('error correction', 'ER'),
            ('ERROR', 'ER'),
            ('additional data', 'AD'),
            ('ADDITIONAL', 'AD'),
            ('new publication', 'NP'),
            ('NEW', 'NP'),
        ]

        for input_type, expected_code in test_cases:
            comment_data = {
                'document_version': self.version.id,
                'content': f'Test comment with type {input_type}?',
                'comment_type': input_type,
                'line_number': 5,
                'doi_requested': False
            }

            response = self.client.post(self.comments_url, comment_data, format='json')
            print(f"Testing {input_type} -> {expected_code}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content.decode()}")

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            comment = Comment.objects.latest('id')
            self.assertEqual(comment.comment_type.code, expected_code)

        # Verify total count
        self.assertEqual(Comment.objects.count(), len(test_cases))
