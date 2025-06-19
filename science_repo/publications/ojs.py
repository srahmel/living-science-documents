import requests
from django.conf import settings
from django.core.exceptions import ValidationError
import json
import logging

logger = logging.getLogger(__name__)


class OJSClient:
    """
    Client for interacting with the Open Journal Systems (OJS) API.

    This client provides methods for:
    - Authenticating with OJS
    - Retrieving publications from OJS
    - Importing publications into the system
    """

    def __init__(self, base_url=None, api_key=None):
        """
        Initialize the OJS client.

        Args:
            base_url (str, optional): The base URL of the OJS instance
            api_key (str, optional): The API key for authentication
        """
        self.base_url = base_url or getattr(settings, 'OJS_BASE_URL', '')
        self.api_key = api_key or getattr(settings, 'OJS_API_KEY', '')

        if not self.base_url:
            raise ValueError("OJS base URL is required")

        if not self.api_key:
            raise ValueError("OJS API key is required")

    def get_headers(self):
        """
        Get the headers for API requests.

        Returns:
            dict: The headers for API requests
        """
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def get_journals(self):
        """
        Get a list of journals from OJS.

        Returns:
            list: A list of journals
        """
        url = f"{self.base_url}/api/v1/journals"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting journals from OJS: {e}")
            raise ValidationError(f"Error getting journals from OJS: {e}")

    def get_issues(self, journal_id):
        """
        Get a list of issues for a journal.

        Args:
            journal_id (int): The ID of the journal

        Returns:
            list: A list of issues
        """
        url = f"{self.base_url}/api/v1/journals/{journal_id}/issues"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting issues from OJS: {e}")
            raise ValidationError(f"Error getting issues from OJS: {e}")

    def get_submissions(self, journal_id, status=None):
        """
        Get a list of submissions for a journal.

        Args:
            journal_id (int): The ID of the journal
            status (str, optional): The status of the submissions to retrieve

        Returns:
            list: A list of submissions
        """
        url = f"{self.base_url}/api/v1/submissions"
        params = {'journalId': journal_id}

        if status:
            params['status'] = status

        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting submissions from OJS: {e}")
            raise ValidationError(f"Error getting submissions from OJS: {e}")

    def get_submission(self, submission_id):
        """
        Get a submission by ID.

        Args:
            submission_id (int): The ID of the submission

        Returns:
            dict: The submission
        """
        url = f"{self.base_url}/api/v1/submissions/{submission_id}"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting submission from OJS: {e}")
            raise ValidationError(f"Error getting submission from OJS: {e}")

    def get_submission_galleys(self, submission_id):
        """
        Get the galleys (publication formats) for a submission.

        Args:
            submission_id (int): The ID of the submission

        Returns:
            list: A list of galleys
        """
        url = f"{self.base_url}/api/v1/submissions/{submission_id}/galleys"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting galleys from OJS: {e}")
            raise ValidationError(f"Error getting galleys from OJS: {e}")

    def get_submission_files(self, submission_id):
        """
        Get the files for a submission.

        Args:
            submission_id (int): The ID of the submission

        Returns:
            list: A list of files
        """
        url = f"{self.base_url}/api/v1/submissions/{submission_id}/files"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting files from OJS: {e}")
            raise ValidationError(f"Error getting files from OJS: {e}")

    def download_file(self, file_id):
        """
        Download a file from OJS.

        Args:
            file_id (int): The ID of the file

        Returns:
            bytes: The file content
        """
        url = f"{self.base_url}/api/v1/files/{file_id}"

        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file from OJS: {e}")
            raise ValidationError(f"Error downloading file from OJS: {e}")

    def import_submission(self, submission_id):
        """
        Import a submission from OJS into the system.

        This method retrieves a submission from OJS and creates a publication
        in the system with the submission data.

        Args:
            submission_id (int): The ID of the submission

        Returns:
            Publication: The created publication
        """
        from publications.models import Publication, DocumentVersion, Author, Keyword
        from django.utils import timezone
        from core.doi import DOIService

        # Get the submission
        submission = self.get_submission(submission_id)

        # Get the galleys
        galleys = self.get_submission_galleys(submission_id)

        # Find a suitable galley (prefer HTML or XML over PDF)
        suitable_galley = None
        for galley in galleys:
            if galley.get('urlPublished'):
                if galley.get('label') in ['HTML', 'XML']:
                    suitable_galley = galley
                    break
                elif galley.get('label') == 'PDF' and not suitable_galley:
                    suitable_galley = galley

        if not suitable_galley:
            raise ValidationError("No suitable galley found for submission")

        # Get the content
        content_url = suitable_galley.get('urlPublished')
        try:
            content_response = requests.get(content_url)
            content_response.raise_for_status()
            content = content_response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting content from OJS: {e}")
            raise ValidationError(f"Error getting content from OJS: {e}")

        # Create or update the publication
        doi = submission.get('doi') or DOIService.generate_doi(entity_type='publication', entity_id=submission_id)

        publication, created = Publication.objects.get_or_create(
            meta_doi=doi,
            defaults={
                'title': submission.get('title', ''),
                'short_title': submission.get('subtitle', ''),
                'status': 'published',
                'created_at': timezone.now(),
            }
        )

        # Create a document version
        version_number = 1
        if not created:
            # If the publication already exists, increment the version number
            latest_version = publication.document_versions.order_by('-version_number').first()
            if latest_version:
                version_number = latest_version.version_number + 1

        document_doi = DOIService.generate_doi(entity_type='document', entity_id=f"{submission_id}_{version_number}")

        document_version = DocumentVersion.objects.create(
            publication=publication,
            version_number=version_number,
            doi=document_doi,
            content=content,
            technical_abstract=submission.get('abstract', ''),
            introduction=submission.get('abstract', ''),  # Use abstract as introduction for now
            methodology='',  # Not available in OJS API
            main_text=content,
            conclusion='',  # Not available in OJS API
            author_contributions='',  # Not available in OJS API
            conflicts_of_interest='',  # Not available in OJS API
            acknowledgments='',  # Not available in OJS API
            funding='',  # Not available in OJS API
            references='',  # Not available in OJS API
            status='published',
            status_date=timezone.now(),
            release_date=timezone.now().date(),
        )

        # Create authors
        for i, author_data in enumerate(submission.get('authors', [])):
            Author.objects.create(
                document_version=document_version,
                name=f"{author_data.get('givenName', '')} {author_data.get('familyName', '')}",
                email=author_data.get('email', ''),
                institution=author_data.get('affiliation', ''),
                orcid=author_data.get('orcid', ''),
                order=i,
                is_corresponding=i == 0,  # Assume first author is corresponding author
            )

        # Create keywords
        for keyword in submission.get('keywords', []):
            Keyword.objects.create(
                document_version=document_version,
                keyword=keyword,
            )

        return publication
