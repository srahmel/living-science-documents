from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from .models import Publication, DocumentVersion, Author, Figure, Table, Keyword, Attachment, ReviewProcess, Reviewer
from .serializers import PublicationSerializer, DocumentVersionSerializer
import json
from django.utils import timezone
import datetime

User = get_user_model()

class PublicationModelTest(TestCase):
    """Test the Publication model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.publication_data = {
            'meta_doi': '10.1234/test.2023.001',
            'title': 'Test Publication',
            'short_title': 'Test Pub',
            'editorial_board': self.user
        }
        self.publication = Publication.objects.create(**self.publication_data)

    def test_publication_creation(self):
        """Test that a publication can be created"""
        self.assertEqual(self.publication.meta_doi, self.publication_data['meta_doi'])
        self.assertEqual(self.publication.title, self.publication_data['title'])
        self.assertEqual(self.publication.short_title, self.publication_data['short_title'])
        self.assertEqual(self.publication.editorial_board, self.user)
        self.assertIsNotNone(self.publication.created_at)

    def test_publication_str_method(self):
        """Test the string representation of a publication"""
        expected_str = self.publication_data['title']
        self.assertEqual(str(self.publication), expected_str)

    def test_current_version(self):
        """Test the current_version method"""
        # No versions yet
        self.assertIsNone(self.publication.current_version())

        # Add a draft version
        version1 = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='draft',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            introduction='Test introduction',
            methodology='Test methodology',
            main_text='Test main text',
            conclusion='Test conclusion',
            author_contributions='Test author contributions',
            references='Test references',
            doi='10.1234/test.2023.001.v1'
        )
        self.assertIsNone(self.publication.current_version())

        # Add a published version
        version2 = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=2,
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract 2',
            introduction='Test introduction 2',
            methodology='Test methodology 2',
            main_text='Test main text 2',
            conclusion='Test conclusion 2',
            author_contributions='Test author contributions 2',
            references='Test references 2',
            doi='10.1234/test.2023.001.v2',
            release_date=timezone.now().date()
        )
        self.assertEqual(self.publication.current_version(), version2)

    def test_latest_version(self):
        """Test the latest_version method"""
        # No versions yet
        self.assertIsNone(self.publication.latest_version())

        # Add a version
        version1 = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='draft',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            introduction='Test introduction',
            methodology='Test methodology',
            main_text='Test main text',
            conclusion='Test conclusion',
            author_contributions='Test author contributions',
            references='Test references',
            doi='10.1234/test.2023.002.v1'
        )
        self.assertEqual(self.publication.latest_version(), version1)

        # Add a newer version
        version2 = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=2,
            status='draft',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract 2',
            introduction='Test introduction 2',
            methodology='Test methodology 2',
            main_text='Test main text 2',
            conclusion='Test conclusion 2',
            author_contributions='Test author contributions 2',
            references='Test references 2',
            doi='10.1234/test.2023.002.v2'
        )
        self.assertEqual(self.publication.latest_version(), version2)


class DocumentVersionModelTest(TestCase):
    """Test the DocumentVersion model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.user
        )
        self.version_data = {
            'publication': self.publication,
            'version_number': 1,
            'status': 'draft',
            'status_date': timezone.now(),
            'status_user': self.user,
            'technical_abstract': 'Test abstract',
            'non_technical_abstract': 'Simple abstract',
            'introduction': 'Test introduction',
            'methodology': 'Test methodology',
            'main_text': 'Test main text',
            'conclusion': 'Test conclusion',
            'author_contributions': 'Test author contributions',
            'conflicts_of_interest': 'Test conflicts of interest',
            'acknowledgments': 'Test acknowledgments',
            'funding': 'Test funding',
            'references': 'Test references',
            'doi': '10.1234/test.2023.001.v1'
        }
        self.version = DocumentVersion.objects.create(**self.version_data)

    def test_document_version_creation(self):
        """Test that a document version can be created"""
        self.assertEqual(self.version.publication, self.publication)
        self.assertEqual(self.version.version_number, self.version_data['version_number'])
        self.assertEqual(self.version.status, self.version_data['status'])
        self.assertEqual(self.version.status_user, self.user)
        self.assertEqual(self.version.technical_abstract, self.version_data['technical_abstract'])
        self.assertEqual(self.version.doi, self.version_data['doi'])
        self.assertIsNone(self.version.reviewer_response)  # Default value should be None

    def test_document_version_str_method(self):
        """Test the string representation of a document version"""
        expected_str = f"{self.publication.title} v{self.version.version_number}"
        self.assertEqual(str(self.version), expected_str)

    def test_reviewer_response_field(self):
        """Test that the reviewer_response field can be updated and retrieved"""
        # Initially the field should be None
        self.assertIsNone(self.version.reviewer_response)

        # Update the field
        test_response = "This is a response to reviewer comments addressing all concerns."
        self.version.reviewer_response = test_response
        self.version.save()

        # Retrieve the updated version and check the field
        updated_version = DocumentVersion.objects.get(id=self.version.id)
        self.assertEqual(updated_version.reviewer_response, test_response)

    def test_document_version_ordering(self):
        """Test that document versions are ordered by version_number"""
        # Create a second version
        version2 = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=2,
            status='draft',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract 2',
            introduction='Test introduction 2',
            methodology='Test methodology 2',
            main_text='Test main text 2',
            conclusion='Test conclusion 2',
            author_contributions='Test author contributions 2',
            references='Test references 2',
            doi='10.1234/test.2023.003.v2'
        )

        # Get all versions
        versions = DocumentVersion.objects.filter(publication=self.publication).order_by('version_number')
        self.assertEqual(versions[0], self.version)  # Lower version number first
        self.assertEqual(versions[1], version2)


class PublicationAPITest(APITestCase):
    """Test the Publication API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.publications_url = reverse('publication-list')

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )

        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        # Create a publication
        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.admin
        )

        # Create a document version
        self.version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

    def test_list_publications_anonymous(self):
        """Test that anonymous users can list publications"""
        response = self.client.get(self.publications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_publication_anonymous(self):
        """Test that anonymous users can retrieve a publication"""
        response = self.client.get(f"{self.publications_url}{self.publication.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta_doi'], self.publication.meta_doi)

    def test_create_publication_anonymous(self):
        """Test that anonymous users cannot create a publication"""
        new_publication_data = {
            'meta_doi': '10.1234/test.2023.002',
            'title': 'New Publication',
            'short_title': 'New Pub'
        }
        response = self.client.post(self.publications_url, new_publication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_publication_regular_user(self):
        """Test that regular users can create a publication"""
        self.client.force_authenticate(user=self.user)
        new_publication_data = {
            'meta_doi': '10.1234/test.2023.002',
            'title': 'New Publication',
            'short_title': 'New Pub'
        }
        response = self.client.post(self.publications_url, new_publication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_publication_admin(self):
        """Test that admin users can create a publication"""
        self.client.force_authenticate(user=self.admin)
        new_publication_data = {
            'meta_doi': '10.1234/test.2023.002',
            'title': 'New Publication',
            'short_title': 'New Pub'
        }
        response = self.client.post(self.publications_url, new_publication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['meta_doi'], new_publication_data['meta_doi'])
        self.assertTrue(Publication.objects.filter(meta_doi='10.1234/test.2023.002').exists())

    def test_update_publication_admin(self):
        """Test that admin users can update a publication"""
        self.client.force_authenticate(user=self.admin)
        update_data = {
            'title': 'Updated Publication',
            'short_title': 'Updated Pub'
        }
        response = self.client.patch(f"{self.publications_url}{self.publication.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.title, update_data['title'])
        self.assertEqual(self.publication.short_title, update_data['short_title'])

    def test_delete_publication_admin(self):
        """Test that admin users can delete a publication"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"{self.publications_url}{self.publication.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Publication.objects.filter(id=self.publication.id).exists())

    def test_versions_endpoint(self):
        """Test the versions endpoint"""
        response = self.client.get(f"{self.publications_url}{self.publication.id}/versions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['version_number'], self.version.version_number)

    def test_current_version_endpoint(self):
        """Test the current_version endpoint"""
        response = self.client.get(f"{self.publications_url}{self.publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version_number'], self.version.version_number)
        self.assertEqual(response.data['doi'], self.version.doi)


class DocumentVersionAPITest(APITestCase):
    """Test the DocumentVersion API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.versions_url = reverse('documentversion-list')

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )

        # Create author user
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpassword123'
        )

        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        # Create a publication
        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.admin
        )

        # Create a document version
        self.version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Test abstract',
            introduction='Test introduction',
            methodology='Test methodology',
            main_text='Test main text',
            conclusion='Test conclusion',
            author_contributions='Test author contributions',
            references='Test references',
            doi='10.1234/test.2023.004.v1',
            release_date=timezone.now().date()
        )

        # Add author to the document version
        self.document_author = Author.objects.create(
            document_version=self.version,
            user=self.author,
            name='Author Name',
            email='author@example.com',
            institution='Test Institution',
            is_corresponding=True
        )

    def test_list_versions_anonymous(self):
        """Test that anonymous users can list document versions"""
        response = self.client.get(self.versions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_version_anonymous(self):
        """Test that anonymous users can retrieve a document version"""
        response = self.client.get(f"{self.versions_url}{self.version.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['doi'], self.version.doi)
        self.assertIn('reviewer_response', response.data)  # Check that reviewer_response field is included

    def test_create_version_anonymous(self):
        """Test that anonymous users cannot create a document version"""
        new_version_data = {
            'publication': self.publication.id,
            'technical_abstract': 'New abstract',
            'doi': '10.1234/test.2023.001.v2'
        }
        response = self.client.post(self.versions_url, new_version_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_version_author(self):
        """Test that authors can create a new document version"""
        self.client.force_authenticate(user=self.author)
        new_version_data = {
            'publication': self.publication.id,
            'version_number': 2,  # Add version_number field
            'content': 'New content',
            'technical_abstract': 'New abstract',
            'introduction': 'New introduction',
            'methodology': 'New methodology',
            'main_text': 'New main text',
            'conclusion': 'New conclusion',
            'author_contributions': 'New author contributions',
            'references': 'New references',
            'doi': '10.1234/test.2023.005.v1'
        }
        response = self.client.post(self.versions_url, new_version_data, format='json')
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['version_number'], 2)  # Auto-incremented
        self.assertEqual(response.data['technical_abstract'], new_version_data['technical_abstract'])
        # DOI is read-only, so we can't set it directly
        self.assertTrue(DocumentVersion.objects.filter(
            version_number=2,
            technical_abstract='New abstract'
        ).exists())

    def test_update_version_author(self):
        """Test that authors can update their document version"""
        self.client.force_authenticate(user=self.author)
        update_data = {
            'technical_abstract': 'Updated abstract',
            'reviewer_response': 'Response to reviewer comments addressing all concerns.'
        }
        response = self.client.patch(f"{self.versions_url}{self.version.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.technical_abstract, update_data['technical_abstract'])
        self.assertEqual(self.version.reviewer_response, update_data['reviewer_response'])

    def test_update_version_non_author(self):
        """Test that non-authors cannot update a document version"""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'technical_abstract': 'Updated abstract'
        }
        response = self.client.patch(f"{self.versions_url}{self.version.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.version.refresh_from_db()
        self.assertNotEqual(self.version.technical_abstract, update_data['technical_abstract'])

    def test_submit_for_review(self):
        """Test the submit_for_review endpoint"""
        self.client.force_authenticate(user=self.author)

        # Create a draft version
        draft_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=2,
            status='draft',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Draft abstract',
            introduction='Draft introduction',
            methodology='Draft methodology',
            main_text='Draft main text',
            conclusion='Draft conclusion',
            author_contributions='Draft author contributions',
            references='Draft references',
            doi='10.1234/test.2023.006.v1'
        )

        # Add author to the draft version
        Author.objects.create(
            document_version=draft_version,
            user=self.author,
            name='Author Name',
            email='author@example.com',
            institution='Test Institution',
            is_corresponding=True
        )

        response = self.client.post(f"{self.versions_url}{draft_version.id}/submit_for_review/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        draft_version.refresh_from_db()
        self.assertEqual(draft_version.status, 'submitted')
