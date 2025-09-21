import urllib.parse
from django.test import TestCase, Client, override_settings
from unittest.mock import patch


@override_settings(ORCID_REDIRECT_URI='https://override.example.org/sso/orcid/callback')
class OrcidRedirectOverrideTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_uses_override_redirect_uri_verbatim(self):
        resp = self.client.get('/api/auth/orcid/login/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('auth_url', data)
        auth_url = data['auth_url']
        parsed = urllib.parse.urlparse(auth_url)
        q = urllib.parse.parse_qs(parsed.query)
        self.assertIn('redirect_uri', q)
        # Exact match, no extra params added
        self.assertEqual(q['redirect_uri'][0], 'https://override.example.org/sso/orcid/callback')

    @patch('core.orcid.ORCIDAuth.extract_user_info', return_value={
        'first_name': 'A', 'last_name': 'B', 'email': '', 'other_names': [],
        'biography': '', 'keywords': [], 'country': '', 'website': ''
    })
    @patch('core.orcid.ORCIDAuth.get_orcid_profile', return_value={})
    @patch('core.orcid.ORCIDAuth.validate_orcid_checksum', return_value=True)
    def test_callback_calls_get_token_with_override(self, *_mocks):
        # Verify get_token called with overridden redirect_uri
        with patch('core.orcid.ORCIDAuth.get_token', return_value={'orcid': '0000-0001-2345-6789', 'access_token': 'tok'}) as mocked_get_token:
            # Seed session state
            session = self.client.session
            session['orcid_oauth_state'] = 'state123'
            session.save()
            resp = self.client.get('/api/auth/orcid/callback/?code=abc&state=state123')
            self.assertEqual(resp.status_code, 302)
            # Assert call args include override
            args, kwargs = mocked_get_token.call_args
            self.assertEqual(args[0], 'abc')
            self.assertEqual(args[1], 'https://override.example.org/sso/orcid/callback')
