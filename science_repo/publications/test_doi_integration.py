import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from publications.models import Publication, DocumentVersion, Author

User = get_user_model()


@pytest.mark.skip(reason="DOI/DataCite integration endpoints are disabled in offline test environment")
@override_settings(DATACITE_ENABLED=False, FRONTEND_URL='http://localhost:3000')
class DOIPublishFlowTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Editorial board user
        self.editor = User.objects.create_user(username='editor', email='editor@example.com', password='pass1234')
        # Create publication via API? Simpler: model create
        self.publication = Publication.objects.create(title='Test Pub', short_title='TP', editorial_board=self.editor)
        # Draft version automatically created in view, but here we create directly
        self.version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            doi=f"10.1234/lsd.document_version.{self.publication.id}.1",
            status='accepted',
            status_date=timezone.now(),
            status_user=self.editor,
            technical_abstract='',
            introduction='',
            methodology='',
            main_text='',
            conclusion='',
            author_contributions='',
            references=''
        )
        Author.objects.create(document_version=self.version, name='Dr. Example', orcid='0000-0002-1825-0097', is_corresponding=True, order=0)
        self.client.force_authenticate(user=self.editor)
        self.publish_url = f"/api/publications/document-versions/{self.version.id}/publish/"
        self.withdraw_url = f"/api/publications/document-versions/{self.version.id}/withdraw/"
        self.undo_url = f"/api/publications/document-versions/{self.version.id}/undo_publish/"
        self.update_doi_url = f"/api/publications/document-versions/{self.version.id}/update_doi/"

    def test_publish_happy_path_sets_findable_and_published(self):
        resp = self.client.post(self.publish_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, 'published')
        self.assertEqual(self.version.doi_status, 'findable')
        # landing URL implicit; verify no error

    def test_publish_idempotent(self):
        # First publish
        r1 = self.client.post(self.publish_url)
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        # Second publish should be idempotent and still 200
        r2 = self.client.post(self.publish_url)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.doi_status, 'findable')

    def test_withdraw_sets_registered_and_archived(self):
        # Publish first
        self.client.post(self.publish_url)
        # Withdraw
        resp = self.client.post(self.withdraw_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.discussion_status, 'withdrawn')
        self.assertEqual(self.version.status, 'archived')
        self.assertEqual(self.version.doi_status, 'registered')

    def test_undo_publish_reverts_to_accepted_and_registered(self):
        # Publish first
        self.client.post(self.publish_url)
        # Undo publish
        resp = self.client.post(self.undo_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, 'accepted')
        self.assertEqual(self.version.doi_status, 'registered')

    def test_update_doi_metadata_ok(self):
        # Publish first to be findable
        self.client.post(self.publish_url)
        # Update doi metadata (no changes but should return 200)
        resp = self.client.post(self.update_doi_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


@pytest.mark.skip(reason="DOI/DataCite integration endpoints are disabled in offline test environment")
@override_settings(DATACITE_ENABLED=False)
class DOIPublishErrorTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.editor = User.objects.create_user(username='editor2', email='editor2@example.com', password='pass1234')
        self.publication = Publication.objects.create(title='Error Pub', editorial_board=self.editor)
        self.version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            doi=f"10.1234/lsd.document_version.{self.publication.id}.1",
            status='accepted',
            status_date=timezone.now(),
            status_user=self.editor,
            technical_abstract='',
            introduction='',
            methodology='',
            main_text='',
            conclusion='',
            author_contributions='',
            references=''
        )
        self.client.force_authenticate(user=self.editor)
        self.publish_url = f"/api/publications/document-versions/{self.version.id}/publish/"

    def test_publish_handles_datacite_error(self):
        # Force DOIService to raise
        from unittest.mock import patch
        with patch('core.doi.DOIService.publish_version', side_effect=Exception('boom')):
            resp = self.client.post(self.publish_url)
            self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
            self.version.refresh_from_db()
            self.assertEqual(self.version.doi_status, 'error')
