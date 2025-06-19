from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.utils import timezone
from .models import AIModel, AIPrompt, AICommentSuggestion, AIPromptLog, AIReference, AIFeedback
from publications.models import Publication, DocumentVersion
from comments.models import Comment, CommentType
import json

User = get_user_model()

class AIModelModelTest(TestCase):
    """Test the AIModel model"""

    def setUp(self):
        self.ai_model_data = {
            'name': 'GPT-4',
            'version': '1.0',
            'provider': 'OpenAI',
            'api_endpoint': 'https://api.openai.com/v1/chat/completions',
            'is_active': True
        }
        self.ai_model = AIModel.objects.create(**self.ai_model_data)

    def test_ai_model_creation(self):
        """Test that an AI model can be created"""
        self.assertEqual(self.ai_model.name, self.ai_model_data['name'])
        self.assertEqual(self.ai_model.version, self.ai_model_data['version'])
        self.assertEqual(self.ai_model.provider, self.ai_model_data['provider'])
        self.assertEqual(self.ai_model.api_endpoint, self.ai_model_data['api_endpoint'])
        self.assertEqual(self.ai_model.is_active, self.ai_model_data['is_active'])

    def test_ai_model_str_method(self):
        """Test the string representation of an AI model"""
        expected_str = f"{self.ai_model_data['name']} v{self.ai_model_data['version']}"
        self.assertEqual(str(self.ai_model), expected_str)


class AIPromptModelTest(TestCase):
    """Test the AIPrompt model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt_data = {
            'name': 'Scientific Question Generator',
            'description': 'Generates scientific questions based on document content',
            'prompt_template': 'Generate a scientific question about the following text: {{text}}',
            'ai_model': self.ai_model,
            'is_active': True,
            'created_by': self.user
        }
        self.ai_prompt = AIPrompt.objects.create(**self.ai_prompt_data)

    def test_ai_prompt_creation(self):
        """Test that an AI prompt can be created"""
        self.assertEqual(self.ai_prompt.name, self.ai_prompt_data['name'])
        self.assertEqual(self.ai_prompt.description, self.ai_prompt_data['description'])
        self.assertEqual(self.ai_prompt.prompt_template, self.ai_prompt_data['prompt_template'])
        self.assertEqual(self.ai_prompt.ai_model, self.ai_model)
        self.assertEqual(self.ai_prompt.is_active, self.ai_prompt_data['is_active'])
        self.assertEqual(self.ai_prompt.created_by, self.user)

    def test_ai_prompt_str_method(self):
        """Test the string representation of an AI prompt"""
        expected_str = self.ai_prompt_data['name']
        self.assertEqual(str(self.ai_prompt), expected_str)


class AICommentSuggestionModelTest(TestCase):
    """Test the AICommentSuggestion model"""

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

        self.document_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt = AIPrompt.objects.create(
            name='Scientific Question Generator',
            description='Generates scientific questions based on document content',
            prompt_template='Generate a scientific question about the following text: {{text}}',
            ai_model=self.ai_model,
            is_active=True,
            created_by=self.user
        )

        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.comment_type,
            content='Is this methodology consistent with previous studies?',
            status='published',
            status_user=self.user,
            doi='10.1234/comment.2023.001',
            is_ai_generated=True
        )

        self.ai_suggestion_data = {
            'document_version': self.document_version,
            'ai_model': self.ai_model,
            'ai_prompt': self.ai_prompt,
            'content': 'Is this methodology consistent with previous studies?',
            'section_reference': 'Methods',
            'line_start': 100,
            'line_end': 120,
            'status': 'approved',
            'reviewed_by': self.user,
            'comment': self.comment,
            'confidence_score': 0.85
        }
        self.ai_suggestion = AICommentSuggestion.objects.create(**self.ai_suggestion_data)

    def test_ai_suggestion_creation(self):
        """Test that an AI comment suggestion can be created"""
        self.assertEqual(self.ai_suggestion.document_version, self.document_version)
        self.assertEqual(self.ai_suggestion.ai_model, self.ai_model)
        self.assertEqual(self.ai_suggestion.ai_prompt, self.ai_prompt)
        self.assertEqual(self.ai_suggestion.content, self.ai_suggestion_data['content'])
        self.assertEqual(self.ai_suggestion.section_reference, self.ai_suggestion_data['section_reference'])
        self.assertEqual(self.ai_suggestion.line_start, self.ai_suggestion_data['line_start'])
        self.assertEqual(self.ai_suggestion.line_end, self.ai_suggestion_data['line_end'])
        self.assertEqual(self.ai_suggestion.status, self.ai_suggestion_data['status'])
        self.assertEqual(self.ai_suggestion.reviewed_by, self.user)
        self.assertEqual(self.ai_suggestion.comment, self.comment)
        self.assertEqual(self.ai_suggestion.confidence_score, self.ai_suggestion_data['confidence_score'])

    def test_ai_suggestion_str_method(self):
        """Test the string representation of an AI comment suggestion"""
        expected_str = f"AI Suggestion for {self.document_version}"
        self.assertEqual(str(self.ai_suggestion), expected_str)


class AIReferenceModelTest(TestCase):
    """Test the AIReference model"""

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

        self.document_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt = AIPrompt.objects.create(
            name='Scientific Question Generator',
            description='Generates scientific questions based on document content',
            prompt_template='Generate a scientific question about the following text: {{text}}',
            ai_model=self.ai_model,
            is_active=True,
            created_by=self.user
        )

        self.ai_suggestion = AICommentSuggestion.objects.create(
            document_version=self.document_version,
            ai_model=self.ai_model,
            ai_prompt=self.ai_prompt,
            content='Is this methodology consistent with previous studies?',
            section_reference='Methods',
            line_start=100,
            line_end=120,
            status='pending',
            confidence_score=0.85
        )

        self.ai_reference_data = {
            'suggestion': self.ai_suggestion,
            'title': 'Test Reference',
            'authors': 'Smith, J., Jones, K.',
            'publication_date': timezone.now().date(),
            'doi': '10.1234/reference.2023.001',
            'url': 'https://example.com/reference',
            'citation_text': 'Smith, J., Jones, K. (2023). Test Reference. Journal of Testing, 1(1), 1-10.',
            'trust_level': 'high'
        }
        self.ai_reference = AIReference.objects.create(**self.ai_reference_data)

    def test_ai_reference_creation(self):
        """Test that an AI reference can be created"""
        self.assertEqual(self.ai_reference.suggestion, self.ai_suggestion)
        self.assertEqual(self.ai_reference.title, self.ai_reference_data['title'])
        self.assertEqual(self.ai_reference.authors, self.ai_reference_data['authors'])
        self.assertEqual(self.ai_reference.publication_date, self.ai_reference_data['publication_date'])
        self.assertEqual(self.ai_reference.doi, self.ai_reference_data['doi'])
        self.assertEqual(self.ai_reference.url, self.ai_reference_data['url'])
        self.assertEqual(self.ai_reference.citation_text, self.ai_reference_data['citation_text'])
        self.assertEqual(self.ai_reference.trust_level, self.ai_reference_data['trust_level'])

    def test_ai_reference_str_method(self):
        """Test the string representation of an AI reference"""
        expected_str = self.ai_reference_data['title']
        self.assertEqual(str(self.ai_reference), expected_str)


class AIFeedbackModelTest(TestCase):
    """Test the AIFeedback model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

        self.publication = Publication.objects.create(
            meta_doi='10.1234/test.2023.001',
            title='Test Publication',
            short_title='Test Pub',
            editorial_board=self.user
        )

        self.document_version = DocumentVersion.objects.create(
            publication=self.publication,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt = AIPrompt.objects.create(
            name='Scientific Question Generator',
            description='Generates scientific questions based on document content',
            prompt_template='Generate a scientific question about the following text: {{text}}',
            ai_model=self.ai_model,
            is_active=True,
            created_by=self.user
        )

        self.ai_suggestion = AICommentSuggestion.objects.create(
            document_version=self.document_version,
            ai_model=self.ai_model,
            ai_prompt=self.ai_prompt,
            content='Is this methodology consistent with previous studies?',
            section_reference='Methods',
            line_start=100,
            line_end=120,
            status='pending',
            confidence_score=0.85
        )

        self.ai_feedback_data = {
            'suggestion': self.ai_suggestion,
            'user': self.user,
            'rating': 4,
            'feedback_text': 'Good suggestion, but could be more specific.'
        }
        self.ai_feedback = AIFeedback.objects.create(**self.ai_feedback_data)

    def test_ai_feedback_creation(self):
        """Test that AI feedback can be created"""
        self.assertEqual(self.ai_feedback.suggestion, self.ai_suggestion)
        self.assertEqual(self.ai_feedback.user, self.user)
        self.assertEqual(self.ai_feedback.rating, self.ai_feedback_data['rating'])
        self.assertEqual(self.ai_feedback.feedback_text, self.ai_feedback_data['feedback_text'])

    def test_ai_feedback_str_method(self):
        """Test the string representation of AI feedback"""
        expected_str = f"Feedback on {self.ai_suggestion} by {self.user.get_full_name()}"
        self.assertEqual(str(self.ai_feedback), expected_str)

    def test_unique_together_constraint(self):
        """Test that a user can only provide feedback once per suggestion"""
        # Try to create another feedback with the same user and suggestion
        with self.assertRaises(Exception):
            AIFeedback.objects.create(
                suggestion=self.ai_suggestion,
                user=self.user,
                rating=3,
                feedback_text='Different feedback'
            )


class AIPromptLogModelTest(TestCase):
    """Test the AIPromptLog model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )

        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt = AIPrompt.objects.create(
            name='Scientific Question Generator',
            description='Generates scientific questions based on document content',
            prompt_template='Generate a scientific question about the following text: {{text}}',
            ai_model=self.ai_model,
            is_active=True,
            created_by=self.user
        )

        self.prompt_log_data = {
            'ai_model': self.ai_model,
            'ai_prompt': self.ai_prompt,
            'user': self.user,
            'input_context': 'The methodology used in this study involves...',
            'output_text': 'Is this methodology consistent with previous studies?',
            'execution_time': 1.25,  # seconds
            'token_count': 150
        }
        self.prompt_log = AIPromptLog.objects.create(**self.prompt_log_data)

    def test_ai_prompt_log_creation(self):
        """Test that an AI prompt log can be created"""
        self.assertEqual(self.prompt_log.ai_model, self.ai_model)
        self.assertEqual(self.prompt_log.ai_prompt, self.ai_prompt)
        self.assertEqual(self.prompt_log.user, self.user)
        self.assertEqual(self.prompt_log.input_context, self.prompt_log_data['input_context'])
        self.assertEqual(self.prompt_log.output_text, self.prompt_log_data['output_text'])
        self.assertEqual(self.prompt_log.execution_time, self.prompt_log_data['execution_time'])
        self.assertEqual(self.prompt_log.token_count, self.prompt_log_data['token_count'])
        self.assertIsNotNone(self.prompt_log.created_at)

    def test_ai_prompt_log_str_method(self):
        """Test the string representation of an AI prompt log"""
        expected_str = f"Log for {self.ai_prompt} at {self.prompt_log.created_at}"
        self.assertEqual(str(self.prompt_log), expected_str)


class AIAssistantAPITest(APITestCase):
    """Test the AI Assistant API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.suggestions_url = reverse('aicommentsuggestion-list')

        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )

        self.editor = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='editorpassword123'
        )

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
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        # Create AI model and prompt
        self.ai_model = AIModel.objects.create(
            name='GPT-4',
            version='1.0',
            provider='OpenAI',
            api_endpoint='https://api.openai.com/v1/chat/completions',
            is_active=True
        )

        self.ai_prompt = AIPrompt.objects.create(
            name='Scientific Question Generator',
            description='Generates scientific questions based on document content',
            prompt_template='Generate a scientific question about the following text: {{text}}',
            ai_model=self.ai_model,
            is_active=True,
            created_by=self.admin
        )

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create an AI suggestion
        self.ai_suggestion = AICommentSuggestion.objects.create(
            document_version=self.document_version,
            ai_model=self.ai_model,
            ai_prompt=self.ai_prompt,
            content='Is this methodology consistent with previous studies?',
            section_reference='Methods',
            line_start=100,
            line_end=120,
            status='pending',
            confidence_score=0.85
        )

    def test_list_suggestions_anonymous(self):
        """Test that anonymous users cannot list AI suggestions"""
        response = self.client.get(self.suggestions_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_suggestions_authenticated(self):
        """Test that authenticated users can list AI suggestions"""
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(self.suggestions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_suggestion_authenticated(self):
        """Test that authenticated users can retrieve an AI suggestion"""
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(f"{self.suggestions_url}{self.ai_suggestion.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], self.ai_suggestion.content)

    def test_generate_suggestions(self):
        """Test the generate_suggestions endpoint"""
        self.client.force_authenticate(user=self.editor)
        generate_url = f"{self.suggestions_url}generate/"
        data = {
            'document_version': self.document_version.id,
            'ai_model': self.ai_model.id,
            'ai_prompt': self.ai_prompt.id
        }
        response = self.client.post(generate_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approve_suggestion(self):
        """Test the approve_suggestion endpoint"""
        self.client.force_authenticate(user=self.editor)
        approve_url = f"{self.suggestions_url}{self.ai_suggestion.id}/approve/"
        response = self.client.post(approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ai_suggestion.refresh_from_db()
        self.assertEqual(self.ai_suggestion.status, 'approved')

        # Check that a comment was created
        self.assertTrue(Comment.objects.filter(ai_suggestion=self.ai_suggestion).exists())
        comment = Comment.objects.get(ai_suggestion=self.ai_suggestion)
        self.assertEqual(comment.content, self.ai_suggestion.content)
        self.assertEqual(comment.is_ai_generated, True)

    def test_reject_suggestion(self):
        """Test the reject_suggestion endpoint"""
        self.client.force_authenticate(user=self.editor)
        reject_url = f"{self.suggestions_url}{self.ai_suggestion.id}/reject/"
        response = self.client.post(reject_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ai_suggestion.refresh_from_db()
        self.assertEqual(self.ai_suggestion.status, 'rejected')

    def test_provide_feedback(self):
        """Test the provide_feedback endpoint"""
        self.client.force_authenticate(user=self.user)
        feedback_url = "/api/ai/ai-feedback/"
        feedback_data = {
            'suggestion': self.ai_suggestion.id,
            'rating': 4,
            'feedback_text': 'Good suggestion, but could be more specific.'
        }
        response = self.client.post(feedback_url, feedback_data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that feedback was created
        self.assertTrue(AIFeedback.objects.filter(suggestion=self.ai_suggestion, user=self.user).exists())
        feedback = AIFeedback.objects.get(suggestion=self.ai_suggestion, user=self.user)
        self.assertEqual(feedback.rating, feedback_data['rating'])
        self.assertEqual(feedback.feedback_text, feedback_data['feedback_text'])
