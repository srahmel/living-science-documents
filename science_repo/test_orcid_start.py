import urllib.parse
from django.test import TestCase, Client, override_settings


class OrcidStartTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_orcid_start_redirects(self):
        resp = self.client.get('/api/auth/orcid/start/')
        # Should redirect to ORCID authorize endpoint
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        self.assertIn('oauth/authorize', location)
        # Has redirect_uri param
        parsed = urllib.parse.urlparse(location)
        q = urllib.parse.parse_qs(parsed.query)
        self.assertIn('redirect_uri', q)
        # Has state param
        self.assertIn('state', q)


@override_settings(FORCE_SCRIPT_NAME='/prefix')
class OrcidStartPrefixedTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_orcid_start_redirect_uri_contains_prefix(self):
        resp = self.client.get('/api/auth/orcid/start/')
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        parsed = urllib.parse.urlparse(location)
        q = urllib.parse.parse_qs(parsed.query)
        self.assertIn('redirect_uri', q)
        redirect_uri = q['redirect_uri'][0]
        self.assertIn('/prefix/api/auth/orcid/callback/', urllib.parse.unquote(redirect_uri))
