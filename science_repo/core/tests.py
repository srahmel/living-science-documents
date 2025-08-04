from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import User
from .serializers import UserSerializer, LoginSerializer, RegistrationSerializer
from django.contrib.auth.models import Group
from unittest.mock import patch
import json

User = get_user_model()

class UserModelTest(TestCase):
    """Test the User model"""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'orcid': '0000-0001-2345-6789',
            'affiliation': 'Test University',
            'research_field': 'Computer Science',
            'qualification': 'PhD'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.first_name, self.user_data['first_name'])
        self.assertEqual(self.user.last_name, self.user_data['last_name'])
        self.assertEqual(self.user.orcid, self.user_data['orcid'])
        self.assertEqual(self.user.affiliation, self.user_data['affiliation'])
        self.assertEqual(self.user.research_field, self.user_data['research_field'])
        self.assertEqual(self.user.qualification, self.user_data['qualification'])
        self.assertTrue(self.user.check_password(self.user_data['password']))

    def test_user_str_method(self):
        """Test the string representation of a user"""
        expected_str = f"{self.user.first_name} {self.user.last_name}"
        self.assertEqual(str(self.user), expected_str)

        # Test with no name
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(str(self.user), self.user.username)


class UserSerializerTest(TestCase):
    """Test the UserSerializer"""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'orcid': '0000-0001-2345-6789',
            'affiliation': 'Test University',
            'research_field': 'Computer Science',
            'qualification': 'PhD'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.serializer = UserSerializer(instance=self.user)

    def test_contains_expected_fields(self):
        """Test that the serializer contains the expected fields"""
        data = self.serializer.data
        self.assertCountEqual(data.keys(), ['id', 'username', 'email', 'first_name', 'last_name', 
                                           'orcid', 'affiliation', 'research_field', 'qualification'])

    def test_field_content(self):
        """Test that the serializer fields contain the expected values"""
        data = self.serializer.data
        self.assertEqual(data['username'], self.user_data['username'])
        self.assertEqual(data['email'], self.user_data['email'])
        self.assertEqual(data['first_name'], self.user_data['first_name'])
        self.assertEqual(data['last_name'], self.user_data['last_name'])
        self.assertEqual(data['orcid'], self.user_data['orcid'])
        self.assertEqual(data['affiliation'], self.user_data['affiliation'])
        self.assertEqual(data['research_field'], self.user_data['research_field'])
        self.assertEqual(data['qualification'], self.user_data['qualification'])


class LoginSerializerTest(TestCase):
    """Test the LoginSerializer"""

    def test_valid_data(self):
        """Test that the serializer validates correct data"""
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_fields(self):
        """Test that the serializer requires all fields"""
        # Missing username
        data = {
            'password': 'testpassword123'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

        # Missing password
        data = {
            'username': 'testuser'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class AuthenticationAPITest(APITestCase):
    """Test the authentication API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_login_valid_credentials(self):
        """Test that a user can login with valid credentials"""
        data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_login_invalid_credentials(self):
        """Test that login fails with invalid credentials"""
        data = {
            'username': self.user_data['username'],
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_fields(self):
        """Test that login fails with missing fields"""
        # Missing username
        data = {
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing password
        data = {
            'username': self.user_data['username']
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserViewSetTest(APITestCase):
    """Test the UserViewSet API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.users_url = reverse('user-list')
        self.logout_url = reverse('logout')
        self.admin_data = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'adminpassword123',
            'is_staff': True,
            'is_superuser': True
        }
        self.admin = User.objects.create_user(**self.admin_data)

        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_list_users_admin(self):
        """Test that an admin can list all users"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # admin and testuser

    def test_list_users_non_admin(self):
        """Test that a non-admin cannot list all users"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_admin(self):
        """Test that an admin can retrieve any user"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.users_url}{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user_data['username'])

    def test_retrieve_user_self(self):
        """Test that a user can retrieve their own profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.users_url}me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user_data['username'])

    def test_retrieve_user_other(self):
        """Test that a user cannot retrieve another user's profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.users_url}{self.admin.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_logout(self):
        """Test that a user can logout successfully"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Successfully logged out.')

    def test_create_user_admin(self):
        """Test that an admin can create a new user"""
        self.client.force_authenticate(user=self.admin)
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.users_url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], new_user_data['username'])
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_create_user_non_admin(self):
        """Test that a non-admin cannot create a new user"""
        self.client.force_authenticate(user=self.user)
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.users_url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_update_user_admin(self):
        """Test that an admin can update any user"""
        self.client.force_authenticate(user=self.admin)
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(f"{self.users_url}{self.user.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data['first_name'])
        self.assertEqual(self.user.last_name, update_data['last_name'])

    def test_update_user_self(self):
        """Test that a user can update their own profile"""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(f"{self.users_url}me/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data['first_name'])
        self.assertEqual(self.user.last_name, update_data['last_name'])

    def test_update_user_other(self):
        """Test that a user cannot update another user's profile"""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(f"{self.users_url}{self.admin.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertNotEqual(self.admin.first_name, update_data['first_name'])

    def test_delete_user_admin(self):
        """Test that an admin can delete any user"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"{self.users_url}{self.user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_delete_user_non_admin(self):
        """Test that a non-admin cannot delete a user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"{self.users_url}{self.admin.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())


class RegistrationAPITest(APITestCase):
    """Test the registration API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'

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

        response = self.client.post(self.register_url, self.valid_data, format='json')
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

        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_registration_missing_required_fields(self):
        """Test that registration fails when required fields are missing"""
        # Test missing email
        data = self.valid_data.copy()
        data.pop('email')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test missing first_name
        data = self.valid_data.copy()
        data.pop('first_name')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

        # Test missing last_name
        data = self.valid_data.copy()
        data.pop('last_name')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data)

        # Test missing dsgvo_consent
        data = self.valid_data.copy()
        data.pop('dsgvo_consent')
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dsgvo_consent', response.data)

    def test_registration_dsgvo_consent_false(self):
        """Test that registration fails when dsgvo_consent is False"""
        data = self.valid_data.copy()
        data['dsgvo_consent'] = False

        response = self.client.post(self.register_url, data, format='json')
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
        response = self.client.post(self.register_url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
