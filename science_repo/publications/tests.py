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

        # Note: In the actual API, a draft version would be automatically created,
        # but since we're using the model directly here, no version is created.

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
        self.publications_url = '/api/publications/publications/'

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

        # Check that the new fields are present in the response
        publication = response.data['results'][0]
        self.assertIn('authors', publication)
        self.assertIn('created_by', publication)
        self.assertIn('metadata', publication)

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
            'meta_doi': '10.1234/test.2023.003',  # Use a different DOI to avoid conflicts
            'title': 'New Publication by Regular User',
            'short_title': 'New Pub User'
        }
        response = self.client.post(self.publications_url, new_publication_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the publication was created
        publication = Publication.objects.get(meta_doi='10.1234/test.2023.003')
        self.assertIsNotNone(publication)

        # Check that a draft version was automatically created
        versions = publication.document_versions.all()
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().status, 'draft')
        self.assertEqual(versions.first().version_number, 1)

        # Check that the current user is set as the author
        self.assertTrue(versions.first().authors.filter(user=self.user).exists())

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

        # Check that the publication was created
        publication = Publication.objects.get(meta_doi='10.1234/test.2023.002')
        self.assertIsNotNone(publication)

        # Check that a draft version was automatically created
        versions = publication.document_versions.all()
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().status, 'draft')
        self.assertEqual(versions.first().version_number, 1)

        # Check that the current user is set as the author
        self.assertTrue(versions.first().authors.filter(user=self.admin).exists())

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

    def test_current_version_endpoint_author_access(self):
        """Test that authors can access the full version details even if there's no published version"""
        # Create a new publication
        publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.003',
            title='Author Access Test Publication',
            short_title='Author Access Test',
            editorial_board=self.admin
        )

        # Create an author user
        author = User.objects.create_user(
            username='authoruser',
            email='author@example.com',
            password='authorpassword123'
        )

        # Create a draft version (not published)
        draft_version = DocumentVersion.objects.create(
            publication=publication,
            version_number=1,
            status='draft',
            status_date=timezone.now(),
            status_user=author,
            technical_abstract='Draft abstract',
            introduction='Draft introduction',
            methodology='Draft methodology',
            main_text='Draft main text',
            conclusion='Draft conclusion',
            author_contributions='Draft author contributions',
            references='Draft references',
            doi='10.1234/test.2023.003.v1'
        )

        # Add author to the draft version
        Author.objects.create(
            document_version=draft_version,
            user=author,
            name='Author Name',
            email='author@example.com',
            institution='Test Institution',
            is_corresponding=True
        )

        # Test anonymous access (should fail as there's no published version)
        response = self.client.get(f"{self.publications_url}{publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test author access (should succeed and return the draft version)
        self.client.force_authenticate(user=author)
        response = self.client.get(f"{self.publications_url}{publication.id}/current_version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version_number'], draft_version.version_number)
        self.assertEqual(response.data['doi'], draft_version.doi)
        self.assertEqual(response.data['technical_abstract'], draft_version.technical_abstract)

        # Verify that all fields needed for editing are present
        self.assertIn('content', response.data)
        self.assertIn('introduction', response.data)
        self.assertIn('methodology', response.data)
        self.assertIn('main_text', response.data)
        self.assertIn('conclusion', response.data)
        self.assertIn('author_contributions', response.data)


class DocumentVersionAPITest(APITestCase):
    """Test the DocumentVersion API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.versions_url = '/api/publications/document-versions/'

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
        """Test that authors can update their document version, creating a new version"""
        self.client.force_authenticate(user=self.author)
        update_data = {
            'technical_abstract': 'Updated abstract',
            'reviewer_response': 'Response to reviewer comments addressing all concerns.'
        }

        # Get the initial version count
        initial_version_count = DocumentVersion.objects.filter(publication=self.publication).count()

        response = self.client.patch(f"{self.versions_url}{self.version.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that a new version was created
        self.assertEqual(DocumentVersion.objects.filter(publication=self.publication).count(), initial_version_count + 1)

        # Get the new version (should be version_number = 2)
        new_version = DocumentVersion.objects.filter(publication=self.publication, version_number=2).first()
        self.assertIsNotNone(new_version)

        # Check that the new version has the updated data
        self.assertEqual(new_version.technical_abstract, update_data['technical_abstract'])
        self.assertEqual(new_version.reviewer_response, update_data['reviewer_response'])

        # Check that the original version is unchanged
        self.version.refresh_from_db()
        self.assertNotEqual(self.version.technical_abstract, update_data['technical_abstract'])
        self.assertNotEqual(self.version.reviewer_response, update_data['reviewer_response'])

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


class ReviewProcessModelTest(TestCase):
    """Test the ReviewProcess model"""

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        # Create a handling editor
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='editorpassword123'
        )

        # Create a publication
        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.user
        )

        # Create a document version
        self.document_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='under_review',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        # Create a review process
        self.review_process_data = {
            'document_version': self.document_version,
            'handling_editor': self.editor,
            'status': 'in_progress',
            'decision': 'Pending review completion'
        }
        self.review_process = ReviewProcess.objects.create(**self.review_process_data)

    def test_review_process_creation(self):
        """Test that a review process can be created"""
        self.assertEqual(self.review_process.document_version, self.document_version)
        self.assertEqual(self.review_process.handling_editor, self.editor)
        self.assertEqual(self.review_process.status, self.review_process_data['status'])
        self.assertEqual(self.review_process.decision, self.review_process_data['decision'])
        self.assertIsNotNone(self.review_process.start_date)
        self.assertIsNone(self.review_process.end_date)

    def test_review_process_str_method(self):
        """Test the string representation of a review process"""
        expected_str = f"Review of {self.document_version}"
        self.assertEqual(str(self.review_process), expected_str)

    def test_review_process_completion(self):
        """Test that a review process can be completed"""
        # Update the review process to completed
        self.review_process.status = 'completed'
        self.review_process.end_date = timezone.now()
        self.review_process.decision = 'Accept with minor revisions'
        self.review_process.save()

        # Refresh from database
        self.review_process.refresh_from_db()

        # Check that the fields were updated
        self.assertEqual(self.review_process.status, 'completed')
        self.assertIsNotNone(self.review_process.end_date)
        self.assertEqual(self.review_process.decision, 'Accept with minor revisions')


class ReviewerModelTest(TestCase):
    """Test the Reviewer model"""

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

        # Create a handling editor
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='editorpassword123'
        )

        # Create a reviewer
        self.reviewer_user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='reviewerpassword123',
            first_name='Review',
            last_name='Expert'
        )

        # Create a publication
        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.user
        )

        # Create a document version
        self.document_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='under_review',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        # Create a review process
        self.review_process = ReviewProcess.objects.create(
            document_version=self.document_version,
            handling_editor=self.editor,
            status='in_progress'
        )

        # Create a reviewer
        self.reviewer_data = {
            'review_process': self.review_process,
            'user': self.reviewer_user,
            'is_active': True
        }
        self.reviewer = Reviewer.objects.create(**self.reviewer_data)

    def test_reviewer_creation(self):
        """Test that a reviewer can be created"""
        self.assertEqual(self.reviewer.review_process, self.review_process)
        self.assertEqual(self.reviewer.user, self.reviewer_user)
        self.assertEqual(self.reviewer.is_active, self.reviewer_data['is_active'])
        self.assertIsNotNone(self.reviewer.invited_at)
        self.assertIsNone(self.reviewer.accepted_at)
        self.assertIsNone(self.reviewer.completed_at)

    def test_reviewer_str_method(self):
        """Test the string representation of a reviewer"""
        expected_str = f"{self.reviewer_user.get_full_name()} reviewing {self.review_process.document_version}"
        self.assertEqual(str(self.reviewer), expected_str)

    def test_reviewer_acceptance(self):
        """Test that a reviewer can accept an invitation"""
        # Update the reviewer to accepted
        self.reviewer.accepted_at = timezone.now()
        self.reviewer.save()

        # Refresh from database
        self.reviewer.refresh_from_db()

        # Check that the fields were updated
        self.assertIsNotNone(self.reviewer.accepted_at)
        self.assertIsNone(self.reviewer.completed_at)

    def test_reviewer_completion(self):
        """Test that a reviewer can complete a review"""
        # Update the reviewer to completed
        self.reviewer.accepted_at = timezone.now() - timezone.timedelta(days=1)
        self.reviewer.completed_at = timezone.now()
        self.reviewer.save()

        # Refresh from database
        self.reviewer.refresh_from_db()

        # Check that the fields were updated
        self.assertIsNotNone(self.reviewer.accepted_at)
        self.assertIsNotNone(self.reviewer.completed_at)
        self.assertTrue(self.reviewer.completed_at > self.reviewer.accepted_at)


class ExportFunctionalityTest(APITestCase):
    """Test the export functionality"""

    def setUp(self):
        # Create a client
        self.client = APIClient()

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
        self.document_version = DocumentVersion.objects.create(
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
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

    @patch('publications.archive.ArchiveService.create_pdf')
    def test_download_pdf(self, mock_create_pdf):
        """Test the download_pdf endpoint"""
        from io import BytesIO

        # Mock the create_pdf method to return a BytesIO object
        pdf_buffer = BytesIO(b'PDF content')
        mock_create_pdf.return_value = pdf_buffer

        # Authenticate as a regular user
        self.client.force_authenticate(user=self.user)

        # Test the endpoint
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/pdf/')

        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the content type is PDF
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Check that the content disposition is correct
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="{self.publication.title}_v{self.document_version.version_number}.pdf"')

        # Check that the create_pdf method was called with the correct arguments
        mock_create_pdf.assert_called_once_with(self.document_version, True)

    @patch('publications.jats_converter.JATSConverter.document_to_jats')
    def test_export_jats(self, mock_document_to_jats):
        """Test the export_jats endpoint"""
        # Mock the document_to_jats method to return XML content
        mock_document_to_jats.return_value = '<article>JATS XML content</article>'

        # Authenticate as a regular user
        self.client.force_authenticate(user=self.user)

        # Test the endpoint
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/jats/')

        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the content type is XML
        self.assertEqual(response['Content-Type'], 'application/xml')

        # Check that the content disposition is correct
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="{self.publication.title}_v{self.document_version.version_number}.xml"')

        # Check that the document_to_jats method was called with the correct arguments
        mock_document_to_jats.assert_called_once_with(self.document_version)

    @patch('publications.jats_converter.JATSConverter.document_to_jats')
    def test_export_to_repository(self, mock_document_to_jats):
        """Test the export_to_repository endpoint"""
        # Mock the document_to_jats method to return XML content
        mock_document_to_jats.return_value = '<article>JATS XML content</article>'

        # Authenticate as a regular user
        self.client.force_authenticate(user=self.user)

        # Test the endpoint with PubMed repository
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/repository/?repository=pubmed')

        # Check that the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the response contains the expected data
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['repository'], 'pubmed')
        self.assertEqual(response.data['repository_name'], 'PubMed Central')
        self.assertEqual(response.data['document_title'], self.publication.title)
        self.assertEqual(response.data['document_version'], self.document_version.version_number)
        self.assertEqual(response.data['doi'], self.document_version.doi)

        # Check that the document_to_jats method was called with the correct arguments
        mock_document_to_jats.assert_called_once_with(self.document_version)

    @patch('publications.jats_converter.JATSConverter.document_to_jats')
    def test_export_to_repository_invalid(self, mock_document_to_jats):
        """Test the export_to_repository endpoint with an invalid repository"""
        # Authenticate as a regular user
        self.client.force_authenticate(user=self.user)

        # Test the endpoint with an invalid repository
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/repository/?repository=invalid')

        # Check that the response is a bad request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that the error message is correct
        self.assertEqual(response.data['error'], 'Unsupported repository: invalid')

        # Check that the document_to_jats method was called with the correct arguments
        mock_document_to_jats.assert_called_once_with(self.document_version)

    def test_export_endpoints_unauthenticated(self):
        """Test that unauthenticated users cannot access export endpoints"""
        # Test the download_pdf endpoint
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/pdf/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test the export_jats endpoint
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/jats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test the export_to_repository endpoint
        response = self.client.get(f'/api/publications/document-versions/{self.document_version.id}/repository/?repository=pubmed')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
