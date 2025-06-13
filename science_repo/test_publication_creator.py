from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from publications.models import Publication
import json

User = get_user_model()

class PublicationCreatorTest(APITestCase):
    """Test that the creator of a publication is properly associated with it"""

    def setUp(self):
        self.client = APIClient()
        self.publications_url = '/api/publications/publications/'

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

    def test_publication_creator_association(self):
        """Test that the creator of a publication is properly associated with it"""
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
        
        # Get the publication details
        response = self.client.get(f"{self.publications_url}{publication_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the editorial_board is set to the user
        self.assertEqual(response.data['editorial_board'], self.user.id)
        
        # Get the publication list to check authors and created_by
        response = self.client.get(self.publications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find our publication in the list
        publication = next((p for p in response.data['results'] if p['id'] == publication_id), None)
        self.assertIsNotNone(publication)
        
        # Check that authors is not empty
        self.assertIsNotNone(publication['authors'])
        self.assertGreater(len(publication['authors']), 0)
        
        # Check that created_by is not null
        self.assertIsNotNone(publication['created_by'])
        
        # Check that the creator's information is correct
        self.assertEqual(publication['created_by']['id'], self.user.id)
        self.assertEqual(publication['created_by']['username'], self.user.username)
        self.assertEqual(publication['created_by']['full_name'], self.user.get_full_name())
        self.assertEqual(publication['created_by']['orcid'], self.user.orcid)
        
        # Check that the user is included in the authors list
        author = publication['authors'][0]
        self.assertEqual(author['user'], self.user.id)
        self.assertEqual(author['name'], self.user.get_full_name())
        self.assertEqual(author['institution'], self.user.affiliation)
        self.assertEqual(author['orcid'], self.user.orcid)
        self.assertEqual(author['user_details']['id'], self.user.id)
        self.assertEqual(author['user_details']['username'], self.user.username)