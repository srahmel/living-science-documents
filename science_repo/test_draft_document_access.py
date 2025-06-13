from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from publications.models import Publication, DocumentVersion, Author
import json

User = get_user_model()

class DraftDocumentAccessTest(APITestCase):
    """Test that authors and editorial office members can view draft documents"""

    def setUp(self):
        self.client = APIClient()
        self.publications_url = '/api/publications/publications/'

        # Create editorial office user
        self.editorial_user = User.objects.create_user(
            username='editorial',
            email='editorial@example.com',
            password='editorialpassword123',
            first_name='Editorial',
            last_name='User'
        )

        # Create author user
        self.author_user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpassword123',
            first_name='Author',
            last_name='User'
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Create a publication with editorial_board set to editorial_user
        self.publication = Publication.objects.create(
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.editorial_user
        )

        # Create a draft document version
        self.draft_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='draft',
            status_date=timezone.now(),
            status_user=self.editorial_user,
            technical_abstract='Draft abstract',
            introduction='Draft introduction',
            methodology='Draft methodology',
            main_text='Draft main text',
            conclusion='Draft conclusion',
            author_contributions='Draft author contributions',
            references='Draft references',
            doi='10.1234/test.2023.001.v1'
        )

        # Add author to the draft version
        Author.objects.create(
            document_version=self.draft_version,
            user=self.author_user,
            name='Author User',
            email='author@example.com',
            institution='Test Institution',
            is_corresponding=True
        )

    def test_editorial_user_can_view_draft(self):
        """Test that editorial office members can view draft documents"""
        self.client.force_authenticate(user=self.editorial_user)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')

    def test_author_can_view_draft(self):
        """Test that authors can view draft documents"""
        self.client.force_authenticate(user=self.author_user)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')

    def test_regular_user_cannot_view_draft(self):
        """Test that regular users cannot view draft documents"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No published version found.')

    def test_anonymous_user_cannot_view_draft(self):
        """Test that anonymous users cannot view draft documents"""
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No published version found.')
