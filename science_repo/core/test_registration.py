from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import User
from .serializers import RegistrationSerializer
from django.contrib.auth.models import Group
from unittest.mock import patch

User = get_user_model()

class RegistrationAPITest(APITestCase):
    """Test the registration API endpoint"""

    def setUp(self):
        self.client = APIClient()

        # Add 'testserver' to ALLOWED_HOSTS
        from django.conf import settings
        settings.ALLOWED_HOSTS.append('testserver')

        # Get or create readers group
        self.readers_group, created = Group.objects.get_or_create(name='readers')

        self.valid_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User',
            'dsgvo_consent': True,
            'affiliation': 'Test University',
            'research_field': 'Computer Science',
            'qualification': 'PhD'
        }

    @patch('core.email.EmailService.send_welcome_email')
    def test_registration_valid_data(self, mock_send_welcome_email):
        """Test that a user can register with valid data"""
        mock_send_welcome_email.return_value = True

        response = self.client.post('/api/auth/auth/register/', self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if user was created
        self.assertTrue(User.objects.filter(username=self.valid_data['username']).exists())
        user = User.objects.get(username=self.valid_data['username'])

        # Check if user data is correct
        self.assertEqual(user.email, self.valid_data['email'])
        self.assertEqual(user.first_name, self.valid_data['first_name'])
        self.assertEqual(user.last_name, self.valid_data['last_name'])
        self.assertEqual(user.affiliation, self.valid_data['affiliation'])
        self.assertEqual(user.research_field, self.valid_data['research_field'])
        self.assertEqual(user.qualification, self.valid_data['qualification'])

        # Check if user is in readers group
        self.assertTrue(user.groups.filter(name='readers').exists())

        # Check if tokens are returned
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)

        # Check if welcome email was sent
        mock_send_welcome_email.assert_called_once_with(user)

    def test_registration_password_mismatch(self):
        """Test that registration fails when passwords don't match"""
        data = self.valid_data.copy()
        data['password2'] = 'differentpassword'

        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_registration_missing_required_fields(self):
        """Test that registration fails when required fields are missing"""
        # Test missing email
        data = self.valid_data.copy()
        data.pop('email')
        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test missing first_name
        data = self.valid_data.copy()
        data.pop('first_name')
        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

        # Test missing last_name
        data = self.valid_data.copy()
        data.pop('last_name')
        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data)

        # Test missing dsgvo_consent
        data = self.valid_data.copy()
        data.pop('dsgvo_consent')
        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dsgvo_consent', response.data)

    def test_registration_dsgvo_consent_false(self):
        """Test that registration fails when dsgvo_consent is False"""
        data = self.valid_data.copy()
        data['dsgvo_consent'] = False

        response = self.client.post('/api/auth/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dsgvo_consent', response.data)
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_registration_duplicate_username(self):
        """Test that registration fails when username already exists"""
        # First create a user
        User.objects.create_user(
            username=self.valid_data['username'],
            email='existing@example.com',
            password='existingpassword123'
        )

        # Try to register with the same username
        response = self.client.post('/api/auth/auth/register/', self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
