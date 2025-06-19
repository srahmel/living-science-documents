import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ValidationError
from core.orcid import ORCIDAuth


class ORCIDAuthTest(TestCase):
    """Test the ORCIDAuth class"""

    def setUp(self):
        """Set up test data"""
        self.redirect_uri = 'http://localhost:8000/api/auth/orcid/callback/'
        self.code = 'test_code'
        self.access_token = 'test_access_token'
        self.orcid_id = '0000-0001-2345-6789'
        self.raw_orcid_id = '0000000123456789'

    def test_get_auth_url(self):
        """Test the get_auth_url method"""
        auth_url = ORCIDAuth.get_auth_url(self.redirect_uri)
        
        # Check that the auth URL contains the expected parameters
        self.assertIn(settings.ORCID_AUTH_URL, auth_url)
        self.assertIn(f'client_id={settings.ORCID_CLIENT_ID}', auth_url)
        self.assertIn('response_type=code', auth_url)
        self.assertIn('scope=/authenticate /read-limited', auth_url)
        self.assertIn(f'redirect_uri={self.redirect_uri}', auth_url)

    @patch('requests.post')
    def test_get_token_success(self, mock_post):
        """Test the get_token method with a successful response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': self.access_token,
            'token_type': 'bearer',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'scope': '/authenticate /read-limited',
            'name': 'Test User',
            'orcid': self.orcid_id
        }
        mock_post.return_value = mock_response

        # Call the method
        token_response = ORCIDAuth.get_token(self.code, self.redirect_uri)

        # Check that the method returns the expected response
        self.assertEqual(token_response['access_token'], self.access_token)
        self.assertEqual(token_response['orcid'], self.orcid_id)

        # Check that the post request was called with the expected arguments
        mock_post.assert_called_once_with(
            settings.ORCID_TOKEN_URL,
            data={
                'client_id': settings.ORCID_CLIENT_ID,
                'client_secret': settings.ORCID_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': self.code,
                'redirect_uri': self.redirect_uri
            }
        )

    @patch('requests.post')
    def test_get_token_failure(self, mock_post):
        """Test the get_token method with a failed response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Call the method and check that it raises a ValidationError
        with self.assertRaises(ValidationError):
            ORCIDAuth.get_token(self.code, self.redirect_uri)

    @patch('requests.get')
    def test_get_orcid_profile_success(self, mock_get):
        """Test the get_orcid_profile method with a successful response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': {
                'given-names': {'value': 'Test'},
                'family-name': {'value': 'User'}
            },
            'emails': {
                'email': [
                    {'email': 'test@example.com', 'primary': True}
                ]
            }
        }
        mock_get.return_value = mock_response

        # Call the method
        profile = ORCIDAuth.get_orcid_profile(self.access_token)

        # Check that the method returns the expected response
        self.assertEqual(profile['name']['given-names']['value'], 'Test')
        self.assertEqual(profile['name']['family-name']['value'], 'User')
        self.assertEqual(profile['emails']['email'][0]['email'], 'test@example.com')

        # Check that the get request was called with the expected arguments
        mock_get.assert_called_once_with(
            f'{settings.ORCID_API_URL}/person',
            headers={
                'Accept': 'application/vnd.orcid+json',
                'Authorization': f'Bearer {self.access_token}'
            }
        )

    @patch('requests.get')
    def test_get_orcid_profile_failure(self, mock_get):
        """Test the get_orcid_profile method with a failed response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        # Call the method and check that it raises a ValidationError
        with self.assertRaises(ValidationError):
            ORCIDAuth.get_orcid_profile(self.access_token)

    @patch('requests.get')
    def test_get_orcid_record_success(self, mock_get):
        """Test the get_orcid_record method with a successful response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'orcid-identifier': {
                'uri': f'https://orcid.org/{self.orcid_id}',
                'path': self.orcid_id
            }
        }
        mock_get.return_value = mock_response

        # Call the method
        record = ORCIDAuth.get_orcid_record(self.access_token, self.orcid_id)

        # Check that the method returns the expected response
        self.assertEqual(record['orcid-identifier']['path'], self.orcid_id)

        # Check that the get request was called with the expected arguments
        mock_get.assert_called_once_with(
            f'{settings.ORCID_API_URL}/{self.orcid_id}/record',
            headers={
                'Accept': 'application/vnd.orcid+json',
                'Authorization': f'Bearer {self.access_token}'
            }
        )

    @patch('requests.get')
    def test_get_orcid_record_failure(self, mock_get):
        """Test the get_orcid_record method with a failed response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        # Call the method and check that it raises a ValidationError
        with self.assertRaises(ValidationError):
            ORCIDAuth.get_orcid_record(self.access_token, self.orcid_id)

    @patch('requests.get')
    def test_get_orcid_works_success(self, mock_get):
        """Test the get_orcid_works method with a successful response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'group': [
                {
                    'work-summary': [
                        {
                            'title': {'title': {'value': 'Test Publication'}},
                            'type': 'journal-article'
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response

        # Call the method
        works = ORCIDAuth.get_orcid_works(self.access_token, self.orcid_id)

        # Check that the method returns the expected response
        self.assertEqual(works['group'][0]['work-summary'][0]['title']['title']['value'], 'Test Publication')

        # Check that the get request was called with the expected arguments
        mock_get.assert_called_once_with(
            f'{settings.ORCID_API_URL}/{self.orcid_id}/works',
            headers={
                'Accept': 'application/vnd.orcid+json',
                'Authorization': f'Bearer {self.access_token}'
            }
        )

    @patch('requests.get')
    def test_get_orcid_works_failure(self, mock_get):
        """Test the get_orcid_works method with a failed response"""
        # Mock the response from the ORCID API
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        # Call the method and check that it raises a ValidationError
        with self.assertRaises(ValidationError):
            ORCIDAuth.get_orcid_works(self.access_token, self.orcid_id)

    def test_format_orcid_id(self):
        """Test the format_orcid_id method"""
        # Test with a raw ORCID ID
        formatted_id = ORCIDAuth.format_orcid_id(self.raw_orcid_id)
        self.assertEqual(formatted_id, self.orcid_id)

        # Test with an already formatted ORCID ID
        formatted_id = ORCIDAuth.format_orcid_id(self.orcid_id)
        self.assertEqual(formatted_id, self.orcid_id)

        # Test with a None value
        formatted_id = ORCIDAuth.format_orcid_id(None)
        self.assertEqual(formatted_id, "")

    def test_get_orcid_url(self):
        """Test the get_orcid_url method"""
        # Test with a raw ORCID ID
        url = ORCIDAuth.get_orcid_url(self.raw_orcid_id)
        self.assertEqual(url, f"https://orcid.org/{self.orcid_id}")

        # Test with an already formatted ORCID ID
        url = ORCIDAuth.get_orcid_url(self.orcid_id)
        self.assertEqual(url, f"https://orcid.org/{self.orcid_id}")

    def test_extract_user_info(self):
        """Test the extract_user_info method"""
        # Create a test profile
        profile = {
            'name': {
                'given-names': {'value': 'Test'},
                'family-name': {'value': 'User'}
            },
            'emails': {
                'email': [
                    {'email': 'test@example.com', 'primary': True}
                ]
            },
            'other-names': {
                'other-name': [
                    {'content': 'Test Alias'}
                ]
            },
            'biography': {
                'content': 'Test biography'
            },
            'keywords': {
                'keyword': [
                    {'content': 'test'},
                    {'content': 'science'}
                ]
            },
            'addresses': {
                'address': [
                    {'country': {'value': 'US'}}
                ]
            },
            'researcher-urls': {
                'researcher-url': [
                    {'url': {'value': 'https://example.com'}}
                ]
            }
        }

        # Call the method
        user_info = ORCIDAuth.extract_user_info(profile)

        # Check that the method returns the expected user info
        self.assertEqual(user_info['first_name'], 'Test')
        self.assertEqual(user_info['last_name'], 'User')
        self.assertEqual(user_info['email'], 'test@example.com')
        self.assertEqual(user_info['other_names'], ['Test Alias'])
        self.assertEqual(user_info['biography'], 'Test biography')
        self.assertEqual(user_info['keywords'], ['test', 'science'])
        self.assertEqual(user_info['country'], 'US')
        self.assertEqual(user_info['website'], 'https://example.com')

        # Test with a minimal profile
        minimal_profile = {}
        user_info = ORCIDAuth.extract_user_info(minimal_profile)
        self.assertEqual(user_info['first_name'], '')
        self.assertEqual(user_info['last_name'], '')
        self.assertEqual(user_info['email'], '')
        self.assertEqual(user_info['other_names'], [])
        self.assertEqual(user_info['biography'], '')
        self.assertEqual(user_info['keywords'], [])
        self.assertEqual(user_info['country'], '')
        self.assertEqual(user_info['website'], '')