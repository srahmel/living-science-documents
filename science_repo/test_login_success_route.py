from django.test import TestCase, Client


class LoginSuccessRouteTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_success_route_without_trailing_slash(self):
        resp = self.client.get('/login/success')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login Success', resp.content)

    def test_login_success_route_with_trailing_slash(self):
        resp = self.client.get('/login/success/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login Success', resp.content)

    def test_api_scoped_login_success_route(self):
        resp = self.client.get('/api/auth/login/success/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login Success', resp.content)
