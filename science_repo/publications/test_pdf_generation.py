from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from unittest.mock import patch, MagicMock
from .models import Publication, DocumentVersion

User = get_user_model()

class TestPDFGeneration(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='x', is_staff=True)
        self.user = User.objects.create_user(username='user', email='user@example.com', password='x')
        self.pub = Publication.objects.create(title='PDF Test', editorial_board=self.admin)
        self.dv = DocumentVersion.objects.create(
            publication=self.pub,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Tech',
            introduction='Intro',
            main_text='Body',
            conclusion='End',
            author_contributions='Contribs',
            references='Ref one',
            doi='10.1234/pdf.v1',
            release_date=timezone.now().date(),
        )

    @patch('publications.archive.HTML')
    @patch('publications.archive.CSS')
    def test_download_pdf_uses_weasyprint_when_available(self, mock_css, mock_html):
        # Mock weasyprint HTML.write_pdf to return bytes
        instance = MagicMock()
        instance.write_pdf.return_value = b'%PDF-1.7 mock pdf bytes'
        mock_html.return_value = instance

        self.client.force_authenticate(user=self.user)
        url = f'/api/publications/document-versions/{self.dv.id}/pdf/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF'))
