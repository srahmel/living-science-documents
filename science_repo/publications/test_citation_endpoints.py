from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from .models import Publication, DocumentVersion, Author

User = get_user_model()

class TestCitationEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='x', is_staff=True)
        self.user = User.objects.create_user(username='user', email='user@example.com', password='x')
        self.pub = Publication.objects.create(title='Citation Test', editorial_board=self.admin)
        self.dv = DocumentVersion.objects.create(
            publication=self.pub,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Tech',
            main_text='Body',
            doi='10.1234/cite.v1',
            release_date=timezone.now().date(),
        )
        Author.objects.create(document_version=self.dv, name='Jane Doe', institution='Inst')

    def test_formats_and_styles(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get('/api/publications/citation/formats/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(any(f['id']=='bibtex' for f in r.data))
        r = self.client.get('/api/publications/citation/styles/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(any(s['id']=='apa' for s in r.data))

    def test_get_citation_bibtex_and_ris(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(f'/api/publications/document-versions/{self.dv.id}/citation/?format=bibtex')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('@article', r.content.decode('utf-8'))
        r = self.client.get(f'/api/publications/document-versions/{self.dv.id}/citation/?format=ris')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('TY  - JOUR', r.content.decode('utf-8'))
