import urllib.parse
from django.test import TestCase, Client, override_settings
from unittest.mock import patch


@override_settings(FORCE_SCRIPT_NAME='/prefix')
class OrcidPrefixedPathsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_orcid_login_redirect_uri_contains_prefix(self):
        resp = self.client.get('/api/auth/orcid/login/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('auth_url', data)
        auth_url = data['auth_url']
        # Quick parse to check redirect_uri query component contains the prefix
        parsed = urllib.parse.urlparse(auth_url)
        q = urllib.parse.parse_qs(parsed.query)
        redirect_uris = q.get('redirect_uri') or q.get('redirect_uri'.encode())
        # When URL is already urlencoded as full string we fallback to substring check
        if redirect_uris:
            self.assertTrue(any('/prefix/api/auth/orcid/callback/' in u for u in redirect_uris))
        else:
            self.assertIn('/prefix/api/auth/orcid/callback/', urllib.parse.unquote(auth_url))

    @patch('core.orcid.ORCIDAuth.extract_user_info', return_value={
        'first_name': 'A', 'last_name': 'B', 'email': '', 'other_names': [],
        'biography': '', 'keywords': [], 'country': '', 'website': ''
    })
    @patch('core.orcid.ORCIDAuth.get_orcid_profile', return_value={})
    @patch('core.orcid.ORCIDAuth.validate_orcid_checksum', return_value=True)
    @patch('core.orcid.ORCIDAuth.get_token', return_value={'orcid': '0000-0001-2345-6789', 'access_token': 'tok'})
    def test_orcid_callback_redirects_to_prefixed_login_success(self, *_mocks):
        # Seed session with state
        session = self.client.session
        session['orcid_oauth_state'] = 'state123'
        session.save()
        resp = self.client.get('/api/auth/orcid/callback/?code=abc&state=state123')
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        # Accept either API-scoped success route (preferred) or root-level route
        self.assertTrue(
            location.startswith('http://testserver/prefix/api/auth/login/success') or
            location.startswith('http://testserver/prefix/login/success')
        )
        # Ensure tokens are passed as query params
        self.assertIn('access=', location)
        self.assertIn('refresh=', location)
