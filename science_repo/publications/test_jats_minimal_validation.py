from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Publication, DocumentVersion, Author, Figure
from .jats_converter import JATSConverter
from .jats_validator import validate_minimal_jats
from io import BytesIO
from PIL import Image

User = get_user_model()

class TestJATSMinimalValidation(TestCase):
    def setUp(self):
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='x', is_staff=True
        )
        # Publication and version
        self.pub = Publication.objects.create(title='JATS Test', editorial_board=self.admin)
        self.dv = DocumentVersion.objects.create(
            publication=self.pub,
            version_number=1,
            status='published',
            status_date=timezone.now(),
            status_user=self.admin,
            technical_abstract='Tech abs',
            introduction='Intro',
            methodology='Methods',
            main_text='Main',
            conclusion='Conc',
            author_contributions='Contribs',
            references='Smith 2020. A paper.',
            doi='10.1234/test.v1',
            release_date=timezone.now().date(),
        )
        Author.objects.create(document_version=self.dv, name='Jane Doe', institution='Inst', address='Addr', orcid='0000-0001-2345-6789')
        # Create an in-memory image for the figure
        img = Image.new('RGB', (10, 10), color='white')
        img_buf = BytesIO()
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        # Save to Django ImageField will require a File, but for schema validation we can set the name
        from django.core.files.base import ContentFile
        fig = Figure(document_version=self.dv, figure_number=1, title='F1', caption='Figure caption', alt_text='Alt text')
        fig.image.save('test.png', ContentFile(img_buf.getvalue()), save=True)
        fig.save()

    def test_jats_validates(self):
        xml = JATSConverter.document_to_jats(self.dv)
        # Should include fig, caption and alt-text
        self.assertIn('<fig', xml)
        self.assertIn('<caption>', xml)
        self.assertIn('<alt-text>', xml)
        # Validate against minimal schema
        validate_minimal_jats(xml)
