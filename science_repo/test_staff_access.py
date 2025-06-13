from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from publications.models import Publication, DocumentVersion, Author
import json

User = get_user_model()

class StaffAccessTest(APITestCase):
    """Test that staff members and superusers can view draft documents"""

    def setUp(self):
        self.client = APIClient()
        self.publications_url = '/api/publications/publications/'

        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Create superuser
        self.superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='superuserpassword123',
            first_name='Super',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Create a publication with editorial_board set to regular_user
        self.publication = Publication.objects.create(
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.regular_user
        )

        # Create a draft document version
        self.draft_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='draft',
            status_date=timezone.now(),
            status_user=self.regular_user,
            technical_abstract='Draft abstract',
            introduction='Draft introduction',
            methodology='Draft methodology',
            main_text='Draft main text',
            conclusion='Draft conclusion',
            author_contributions='Draft author contributions',
            references='Draft references',
            doi='10.1234/test.2023.001.v1'
        )

    def test_staff_can_view_draft(self):
        """Test that staff members can view draft documents"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')

    def test_superuser_can_view_draft(self):
        """Test that superusers can view draft documents"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')

    def test_regular_user_cannot_view_draft(self):
        """Test that regular users cannot view draft documents they don't own"""
        # Create another regular user who is not the editorial board member or author
        another_user = User.objects.create_user(
            username='another',
            email='another@example.com',
            password='anotherpassword123'
        )
        
        self.client.force_authenticate(user=another_user)
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'No published version found.')