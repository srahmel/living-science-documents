from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.utils import timezone
from .models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration, CommentChat, ChatMessage
from publications.models import Publication, DocumentVersion, Author
import json

User = get_user_model()

class CommentTypeModelTest(TestCase):
    """Test the CommentType model"""

    def setUp(self):
        self.comment_type_data = {
            'code': 'SC',
            'name': 'Scientific Comment',
            'description': 'A scientific comment on the document',
            'requires_doi': True
        }
        self.comment_type = CommentType.objects.create(**self.comment_type_data)

    def test_comment_type_creation(self):
        """Test that a comment type can be created"""
        self.assertEqual(self.comment_type.code, self.comment_type_data['code'])
        self.assertEqual(self.comment_type.name, self.comment_type_data['name'])
        self.assertEqual(self.comment_type.description, self.comment_type_data['description'])
        self.assertEqual(self.comment_type.requires_doi, self.comment_type_data['requires_doi'])

    def test_comment_type_str_method(self):
        """Test the string representation of a comment type"""
        expected_str = f"{self.comment_type_data['code']} - {self.comment_type_data['name']}"
        self.assertEqual(str(self.comment_type), expected_str)


class CommentModelTest(TestCase):
    """Test the Comment model"""

    def setUp(self):
        # Create a user
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
            editorial_board=self.user
        )

        # Create a document version
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

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create a comment
        self.comment_data = {
            'document_version': self.document_version,
            'comment_type': self.comment_type,
            'content': 'Is this methodology consistent with previous studies?',
            'referenced_text': 'The methodology used in this study...',
            'section_reference': 'Methods',
            'line_start': 100,
            'line_end': 120,
            'status': 'published',
            'status_user': self.user,
            'doi': '10.1234/comment.2023.001'
        }
        self.comment = Comment.objects.create(**self.comment_data)

        # Add an author to the comment
        self.comment_author = CommentAuthor.objects.create(
            comment=self.comment,
            user=self.user,
            is_corresponding=True
        )

    def test_comment_creation(self):
        """Test that a comment can be created"""
        self.assertEqual(self.comment.document_version, self.document_version)
        self.assertEqual(self.comment.comment_type, self.comment_type)
        self.assertEqual(self.comment.content, self.comment_data['content'])
        self.assertEqual(self.comment.referenced_text, self.comment_data['referenced_text'])
        self.assertEqual(self.comment.section_reference, self.comment_data['section_reference'])
        self.assertEqual(self.comment.line_start, self.comment_data['line_start'])
        self.assertEqual(self.comment.line_end, self.comment_data['line_end'])
        self.assertEqual(self.comment.status, self.comment_data['status'])
        self.assertEqual(self.comment.status_user, self.user)
        self.assertEqual(self.comment.doi, self.comment_data['doi'])

    def test_comment_str_method(self):
        """Test the string representation of a comment"""
        expected_str = f"{self.comment_type.code} on {self.document_version} by {self.user.get_full_name()}"
        self.assertEqual(str(self.comment), expected_str)

    def test_is_question(self):
        """Test the is_question method"""
        # Comment ends with a question mark
        self.assertTrue(self.comment.is_question())

        # Comment doesn't end with a question mark
        self.comment.content = 'This is not a question'
        self.comment.save()
        self.assertFalse(self.comment.is_question())


class CommentAuthorModelTest(TestCase):
    """Test the CommentAuthor model"""

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
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
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create a comment
        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.comment_type,
            content='Is this methodology consistent with previous studies?',
            status='published',
            status_user=self.user,
            doi='10.1234/comment.2023.001'
        )

        # Create a comment author
        self.comment_author_data = {
            'comment': self.comment,
            'user': self.user,
            'is_corresponding': True
        }
        self.comment_author = CommentAuthor.objects.create(**self.comment_author_data)

    def test_comment_author_creation(self):
        """Test that a comment author can be created"""
        self.assertEqual(self.comment_author.comment, self.comment)
        self.assertEqual(self.comment_author.user, self.user)
        self.assertEqual(self.comment_author.is_corresponding, self.comment_author_data['is_corresponding'])

    def test_comment_author_str_method(self):
        """Test the string representation of a comment author"""
        expected_str = f"{self.user.get_full_name()} on {self.comment}"
        self.assertEqual(str(self.comment_author), expected_str)

    def test_unique_together_constraint(self):
        """Test that a user can only be an author of a comment once"""
        # Try to create another comment author with the same user and comment
        with self.assertRaises(Exception):
            CommentAuthor.objects.create(
                comment=self.comment,
                user=self.user,
                is_corresponding=False
            )


class CommentReferenceModelTest(TestCase):
    """Test the CommentReference model"""

    def setUp(self):
        # Create a user
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
            editorial_board=self.user
        )

        # Create a document version
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

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create a comment
        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.comment_type,
            content='Is this methodology consistent with previous studies?',
            status='published',
            status_user=self.user,
            doi='10.1234/comment.2023.001'
        )

        # Create a comment reference
        self.reference_data = {
            'comment': self.comment,
            'title': 'Test Reference',
            'authors': 'Smith, J., Jones, K.',
            'publication_date': timezone.now().date(),
            'doi': '10.1234/reference.2023.001',
            'url': 'https://example.com/reference',
            'citation_text': 'Smith, J., Jones, K. (2023). Test Reference. Journal of Testing, 1(1), 1-10.',
            'trust_level': 'high'
        }
        self.reference = CommentReference.objects.create(**self.reference_data)

    def test_comment_reference_creation(self):
        """Test that a comment reference can be created"""
        self.assertEqual(self.reference.comment, self.comment)
        self.assertEqual(self.reference.title, self.reference_data['title'])
        self.assertEqual(self.reference.authors, self.reference_data['authors'])
        self.assertEqual(self.reference.publication_date, self.reference_data['publication_date'])
        self.assertEqual(self.reference.doi, self.reference_data['doi'])
        self.assertEqual(self.reference.url, self.reference_data['url'])
        self.assertEqual(self.reference.citation_text, self.reference_data['citation_text'])
        self.assertEqual(self.reference.trust_level, self.reference_data['trust_level'])

    def test_comment_reference_str_method(self):
        """Test the string representation of a comment reference"""
        expected_str = self.reference_data['title']
        self.assertEqual(str(self.reference), expected_str)


class CommentChatModelTest(TestCase):
    """Test the CommentChat model"""

    def setUp(self):
        # Create a user
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
            editorial_board=self.user
        )

        # Create a document version
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

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create a comment
        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.comment_type,
            content='Is this methodology consistent with previous studies?',
            status='published',
            status_user=self.user,
            doi='10.1234/comment.2023.001'
        )

        # Create a comment chat
        self.chat = CommentChat.objects.create(
            comment=self.comment
        )

    def test_comment_chat_creation(self):
        """Test that a comment chat can be created"""
        self.assertEqual(self.chat.comment, self.comment)
        self.assertIsNotNone(self.chat.created_at)
        self.assertIsNotNone(self.chat.updated_at)

    def test_comment_chat_str_method(self):
        """Test the string representation of a comment chat"""
        expected_str = f"Chat for {self.comment}"
        self.assertEqual(str(self.chat), expected_str)


class ChatMessageModelTest(TestCase):
    """Test the ChatMessage model"""

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
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
            status='published',
            status_date=timezone.now(),
            status_user=self.user,
            technical_abstract='Test abstract',
            doi='10.1234/test.2023.001.v1',
            release_date=timezone.now().date()
        )

        # Create a comment type
        self.comment_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        # Create a comment
        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.comment_type,
            content='Is this methodology consistent with previous studies?',
            status='published',
            status_user=self.user,
            doi='10.1234/comment.2023.001'
        )

        # Create a comment chat
        self.chat = CommentChat.objects.create(
            comment=self.comment
        )

        # Create a chat message
        self.message_data = {
            'chat': self.chat,
            'user': self.user,
            'content': 'This is a test message'
        }
        self.message = ChatMessage.objects.create(**self.message_data)

    def test_chat_message_creation(self):
        """Test that a chat message can be created"""
        self.assertEqual(self.message.chat, self.chat)
        self.assertEqual(self.message.user, self.user)
        self.assertEqual(self.message.content, self.message_data['content'])
        self.assertIsNotNone(self.message.created_at)
        self.assertIsNotNone(self.message.updated_at)

    def test_chat_message_str_method(self):
        """Test the string representation of a chat message"""
        expected_str = f"Message by {self.user.get_full_name()} in {self.chat}"
        self.assertEqual(str(self.message), expected_str)

    def test_chat_message_ordering(self):
        """Test that chat messages are ordered by created_at"""
        # Create a second message
        message2 = ChatMessage.objects.create(
            chat=self.chat,
            user=self.user,
            content='This is a second test message'
        )

        # Get all messages
        messages = ChatMessage.objects.filter(chat=self.chat)
        self.assertEqual(messages[0], self.message)  # First message first
        self.assertEqual(messages[1], message2)


class CommentAPITest(APITestCase):
    """Test the Comment API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.comments_url = reverse('comment-list')

        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword123',
            is_staff=True,
            is_superuser=True
        )

        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@example.com',
            password='moderatorpassword123'
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        # Create commentators group and add user to it
        self.commentators_group, created = Group.objects.get_or_create(name='commentators')
        self.user.groups.add(self.commentators_group)

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

        # Create comment types
        self.sc_type = CommentType.objects.create(
            code='SC',
            name='Scientific Comment',
            description='A scientific comment on the document',
            requires_doi=True
        )

        self.er_type = CommentType.objects.create(
            code='ER',
            name='Error Correction',
            description='A correction of an error in the document',
            requires_doi=False
        )

        # Create a comment
        self.comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.sc_type,
            content='Is this methodology consistent with previous studies?',
            referenced_text='The methodology used in this study...',
            section_reference='Methods',
            line_start=100,
            line_end=120,
            status='published',
            status_user=self.admin,
            doi='10.1234/comment.2023.001'
        )

        # Add an author to the comment
        self.comment_author = CommentAuthor.objects.create(
            comment=self.comment,
            user=self.user,
            is_corresponding=True
        )

    def test_list_comments_anonymous(self):
        """Test that anonymous users can list comments"""
        response = self.client.get(self.comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_comment_anonymous(self):
        """Test that anonymous users can retrieve a comment"""
        response = self.client.get(f"{self.comments_url}{self.comment.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], self.comment.content)

    def test_create_comment_anonymous(self):
        """Test that anonymous users cannot create a comment"""
        new_comment_data = {
            'document_version': self.document_version.id,
            'comment_type': self.sc_type.id,
            'content': 'Is this a new finding compared to previous research?',
            'referenced_text': 'The findings of this study...',
            'section_reference': 'Results',
            'line_start': 200,
            'line_end': 220
        }
        response = self.client.post(self.comments_url, new_comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_authenticated(self):
        """Test that authenticated users can create a comment"""
        self.client.force_authenticate(user=self.user)
        new_comment_data = {
            'document_version': self.document_version.id,
            'comment_type': self.sc_type.id,
            'content': 'Is this a new finding compared to previous research?',
            'referenced_text': 'The findings of this study...',
            'section_reference': 'Results',
            'line_start': 200,
            'line_end': 220
        }
        response = self.client.post(self.comments_url, new_comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], new_comment_data['content'])
        self.assertEqual(response.data['status'], 'draft')  # Default status

        # Check that the user is automatically added as an author
        comment_id = response.data['id']
        comment = Comment.objects.get(id=comment_id)
        self.assertTrue(comment.authors.filter(user=self.user).exists())

    def test_update_comment_author(self):
        """Test that the author can update their comment"""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'content': 'Is this methodology really consistent with previous studies?'
        }
        response = self.client.patch(f"{self.comments_url}{self.comment.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, update_data['content'])

    def test_update_comment_non_author(self):
        """Test that non-authors cannot update a comment"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword123'
        )
        self.client.force_authenticate(user=other_user)
        update_data = {
            'content': 'Is this methodology really consistent with previous studies?'
        }
        response = self.client.patch(f"{self.comments_url}{self.comment.id}/", update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.comment.refresh_from_db()
        self.assertNotEqual(self.comment.content, update_data['content'])

    def test_submit_comment(self):
        """Test the submit_comment endpoint"""
        # Create a draft comment
        draft_comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.sc_type,
            content='Is this a draft comment?',
            status='draft',
            status_user=self.user
        )

        # Add the user as an author
        CommentAuthor.objects.create(
            comment=draft_comment,
            user=self.user,
            is_corresponding=True
        )

        # Submit the comment
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.comments_url}{draft_comment.id}/submit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        draft_comment.refresh_from_db()
        self.assertEqual(draft_comment.status, 'under_review')

    def test_moderate_comment(self):
        """Test the moderate_comment endpoint"""
        # Create a submitted comment
        submitted_comment = Comment.objects.create(
            document_version=self.document_version,
            comment_type=self.sc_type,
            content='Is this a submitted comment?',
            status='submitted',
            status_user=self.user
        )

        # Add the user as an author
        CommentAuthor.objects.create(
            comment=submitted_comment,
            user=self.user,
            is_corresponding=True
        )

        # Moderate the comment
        self.client.force_authenticate(user=self.moderator)
        moderation_data = {
            'decision': 'approved',
            'decision_reason': 'Good comment'
        }
        response = self.client.post(f"{self.comments_url}{submitted_comment.id}/moderate/", moderation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submitted_comment.refresh_from_db()
        self.assertEqual(submitted_comment.status, 'accepted')

        # Check that a moderation record was created
        self.assertTrue(CommentModeration.objects.filter(comment=submitted_comment, moderator=self.moderator).exists())
        moderation = CommentModeration.objects.get(comment=submitted_comment)
        self.assertEqual(moderation.decision, moderation_data['decision'])
        self.assertEqual(moderation.decision_reason, moderation_data['decision_reason'])
