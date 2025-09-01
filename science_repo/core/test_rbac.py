from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.models import AuditLog

User = get_user_model()

class RoleManagementAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Ensure groups
        for name in ['readers','commentators','authors','moderators','review_editors','editorial_office','admins']:
            Group.objects.get_or_create(name=name)
        # Users
        self.admin = User.objects.create_user(username='adminx', email='a@e.com', password='pw', is_superuser=True, is_staff=True)
        self.editorial = User.objects.create_user(username='editorialx', email='e@e.com', password='pw', is_staff=True)
        self.editorial.groups.add(Group.objects.get(name='editorial_office'))
        self.normal = User.objects.create_user(username='normalx', email='n@e.com', password='pw')
        self.target = User.objects.create_user(username='targetx', email='t@e.com', password='pw')
        self.url = reverse('role-management')

    def test_get_roles_requires_privilege(self):
        # Unauthenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Normal authenticated
        self.client.force_authenticate(self.normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_assign_role_and_audit(self):
        self.client.force_authenticate(self.admin)
        payload = {'user_id': self.target.id, 'role': 'authors', 'action': 'add'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.target.groups.filter(name='authors').exists())
        # Audit
        entry = AuditLog.objects.latest('created_at')
        self.assertEqual(entry.action, 'role_add')
        self.assertEqual(entry.target_id, str(self.target.id))
        self.assertIn('authors', entry.after_data['groups'])

    def test_editorial_office_can_assign_role(self):
        self.client.force_authenticate(self.editorial)
        payload = {'user_id': self.target.id, 'role': 'commentators', 'action': 'add'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.target.groups.filter(name='commentators').exists())

    def test_normal_user_cannot_assign_role(self):
        self.client.force_authenticate(self.normal)
        payload = {'user_id': self.target.id, 'role': 'authors', 'action': 'add'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(self.target.groups.filter(name='authors').exists())
