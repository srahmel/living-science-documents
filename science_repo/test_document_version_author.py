from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from publications.models import Publication, DocumentVersion, Author
import json

User = get_user_model()

class DocumentVersionAuthorTest(APITestCase):
    """Test that the creator of a document version is properly associated with it as an author"""

    def setUp(self):
        self.client = APIClient()
        self.publications_url = '/api/publications/publications/'
        self.document_versions_url = '/api/publications/document-versions/'

        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            affiliation='Test Institution',
            orcid='0000-0001-2345-6789'
        )

    def test_document_version_author_association(self):
        """Test that the creator of a document version is properly associated with it as an author"""
        # Authenticate as the user
        self.client.force_authenticate(user=self.user)

        # Create a publication
        publication_data = {
            'title': 'Test Publication',
            'short_title': 'Test Pub'
        }
        response = self.client.post(self.publications_url, publication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the publication ID
        publication_id = response.data['id']
        
        # Create a document version
        document_version_data = {
            'publication': publication_id,
            'content': 'Test content',
            'technical_abstract': 'Test abstract',
            'introduction': 'Test introduction',
            'methodology': 'Test methodology',
            'main_text': 'Test main text',
            'conclusion': 'Test conclusion',
            'author_contributions': 'Test author contributions',
            'references': 'Test references'
        }
        response = self.client.post(self.document_versions_url, document_version_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Get the document version ID
        document_version_id = response.data['id']
        
        # Get the document version details
        response = self.client.get(f"{self.document_versions_url}{document_version_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the user is automatically added as an author
        self.assertIsNotNone(response.data['authors'])
        self.assertGreater(len(response.data['authors']), 0)
        
        # Check that the author's information is correct
        author = response.data['authors'][0]
        self.assertEqual(author['user'], self.user.id)
        self.assertEqual(author['name'], self.user.get_full_name())
        self.assertEqual(author['email'], self.user.email)
        self.assertEqual(author['institution'], self.user.affiliation)
        self.assertEqual(author['orcid'], self.user.orcid)
        self.assertTrue(author['is_corresponding'])
        self.assertEqual(author['order'], 0)