from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from publications.models import Publication
import json

User = get_user_model()

class PublicationNoVersionsTest(APITestCase):
    """Test that users with access can view publications with no versions

    Note: With the changes to automatically create a draft version when a publication is created
    through the API, this scenario (a publication with no versions) will no longer occur in practice.
    However, these tests are still valid for testing the behavior of the current_version endpoint
    when a publication has no versions, which can happen if a publication is created directly
    using the model, bypassing the API.
    """

    def setUp(self):
        self.client = APIClient()
        self.publications_url = '/api/publications/publications/'

        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

        # Create a publication with the user as editorial_board
        self.publication = Publication.objects.create(
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.user
        )

    def test_user_can_view_publication_with_no_versions(self):
        """Test that a user who is the editorial board can view a publication with no versions"""
        # Authenticate as the user
        self.client.force_authenticate(user=self.user)

        # Try to get the current version of the publication
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")

        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the response contains the custom message
        self.assertEqual(response.data['publication_id'], self.publication.id)
        self.assertEqual(response.data['title'], self.publication.title)
        self.assertEqual(response.data['message'], 'This publication exists but has no versions yet.')

    def test_other_user_cannot_view_publication_with_no_versions(self):
        """Test that a user who is not the editorial board cannot view a publication with no versions"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword123'
        )

        # Authenticate as the other user
        self.client.force_authenticate(user=other_user)

        # Try to get the current version of the publication
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")

        # Check that the response is a 404 error
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Check that the response contains the error message
        self.assertEqual(response.data['error'], 'No published version found.')
