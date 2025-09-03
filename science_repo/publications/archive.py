import requests
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
import os
import tempfile
from io import BytesIO
# Placeholders for weasyprint symbols to enable patching in tests
HTML = None
CSS = None
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    _REPORTLAB_AVAILABLE = True
except Exception:
    _REPORTLAB_AVAILABLE = False
    # Provide lightweight fallbacks to keep type names referenced below
    canvas = None
    letter = None
    def getSampleStyleSheet():
        return {'Title': None, 'Normal': None, 'Heading2': None, 'Heading1': None, 'Heading3': None, 'Heading4': None}
    class SimpleDocTemplate:
        def __init__(self, *a, **kw):
            pass
        def build(self, *a, **kw):
            pass
    class Paragraph:
        def __init__(self, *a, **kw):
            pass
    class Spacer:
        def __init__(self, *a, **kw):
            pass
    class Table:
        def __init__(self, *a, **kw):
            pass
    class TableStyle:
        def __init__(self, *a, **kw):
            pass
    colors = object()

logger = logging.getLogger(__name__)


class ArchiveService:
    """
    Service for archiving publications and comments.
    
    This service provides methods for:
    - Creating PDF/A documents from publications and comments
    - Archiving documents in Reposis
    """
    
    @staticmethod
    def create_pdf(document_version, include_comments=True):
        """
        Create a PDF/A document from a document version.
        
        Args:
            document_version: The document version to create a PDF from
            include_comments (bool): Whether to include comments in the PDF
            
        Returns:
            BytesIO: The PDF document as a BytesIO object
        """
        from comments.models import Comment
        from .jats_converter import JATSConverter
        
        # Prefer WeasyPrint to produce PDF/A if available
        try:
            from weasyprint import HTML, CSS
            weasy_available = True
        except Exception:
            weasy_available = False
        
        if weasy_available:
            # Convert to JATS-HTML and render with CSS
            jats_xml = JATSConverter.document_to_jats(document_version)
            html_str = JATSConverter.jats_to_html(jats_xml)
            # Optionally append comments as a section
            if include_comments:
                from django.utils.html import escape
                from comments.models import Comment as Cmt
                comments = Cmt.objects.filter(document_version=document_version, status='published').select_related('comment_type').prefetch_related('authors')
                if comments.exists():
                    html_str += '<h1>Comments</h1>'
                    for c in comments:
                        authors = ', '.join([a.user.get_full_name() for a in c.authors.all()])
                        html_str += f"<h3>{escape(c.comment_type.name)} by {escape(authors)}</h3>"
                        if c.doi:
                            html_str += f"<p>DOI: {escape(c.doi)}</p>"
                        html_str += f"<p>{escape(c.content)}</p>"
            css_path = os.path.join(os.path.dirname(__file__), 'static', 'pdf', 'pdf.css')
            html = HTML(string=html_str, base_url=os.getcwd())
            css = CSS(filename=css_path)
            pdf_bytes = html.write_pdf(stylesheets=[css], presentational_hints=True, optimize_size=('images',), pdf_version='1.7', pdfa='2b')
            return BytesIO(pdf_bytes)
        
        # Fallback to ReportLab (not strict PDF/A)
        # Create a BytesIO object to store the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title_style = styles['Title']
        elements.append(Paragraph(document_version.publication.title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add authors
        authors = [f"{author.name} ({author.institution})" for author in document_version.authors.all()]
        authors_text = ", ".join(authors)
        elements.append(Paragraph(f"Authors: {authors_text}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add DOI
        elements.append(Paragraph(f"DOI: {document_version.doi}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add version
        elements.append(Paragraph(f"Version: {document_version.version_number}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add technical abstract
        if document_version.technical_abstract:
            elements.append(Paragraph("Technical Abstract", styles['Heading2']))
            elements.append(Paragraph(document_version.technical_abstract, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add introduction
        if document_version.introduction:
            elements.append(Paragraph("Introduction", styles['Heading2']))
            elements.append(Paragraph(document_version.introduction, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add methodology
        if document_version.methodology:
            elements.append(Paragraph("Methodology", styles['Heading2']))
            elements.append(Paragraph(document_version.methodology, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add main text
        if document_version.main_text:
            elements.append(Paragraph("Main Text", styles['Heading2']))
            elements.append(Paragraph(document_version.main_text, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add conclusion
        if document_version.conclusion:
            elements.append(Paragraph("Conclusion", styles['Heading2']))
            elements.append(Paragraph(document_version.conclusion, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add author contributions
        if document_version.author_contributions:
            elements.append(Paragraph("Author Contributions", styles['Heading2']))
            elements.append(Paragraph(document_version.author_contributions, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add conflicts of interest
        if document_version.conflicts_of_interest:
            elements.append(Paragraph("Conflicts of Interest", styles['Heading2']))
            elements.append(Paragraph(document_version.conflicts_of_interest, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add acknowledgments
        if document_version.acknowledgments:
            elements.append(Paragraph("Acknowledgments", styles['Heading2']))
            elements.append(Paragraph(document_version.acknowledgments, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add funding
        if document_version.funding:
            elements.append(Paragraph("Funding", styles['Heading2']))
            elements.append(Paragraph(document_version.funding, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add references
        if document_version.references:
            elements.append(Paragraph("References", styles['Heading2']))
            elements.append(Paragraph(document_version.references, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Add comments
        if include_comments:
            comments = Comment.objects.filter(
                document_version=document_version,
                status='published'
            ).select_related('comment_type').prefetch_related('authors', 'references')
            
            if comments.exists():
                elements.append(Paragraph("Comments", styles['Heading1']))
                elements.append(Spacer(1, 12))
                
                for comment in comments:
                    # Add comment type and authors
                    comment_authors = [f"{author.user.get_full_name()}" for author in comment.authors.all()]
                    comment_authors_text = ", ".join(comment_authors)
                    elements.append(Paragraph(f"{comment.comment_type.name} by {comment_authors_text}", styles['Heading3']))
                    
                    # Add comment DOI if available
                    if comment.doi:
                        elements.append(Paragraph(f"DOI: {comment.doi}", styles['Normal']))
                    
                    # Add comment content
                    elements.append(Paragraph(comment.content, styles['Normal']))
                    
                    # Add comment references
                    if comment.references.exists():
                        elements.append(Paragraph("References:", styles['Heading4']))
                        for reference in comment.references.all():
                            elements.append(Paragraph(reference.citation_text, styles['Normal']))
                    
                    elements.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(elements)
        
        # Reset the buffer position to the beginning
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def archive_in_reposis(document_version, include_comments=True):
        """
        Archive a document version in Reposis.
        
        Args:
            document_version: The document version to archive
            include_comments (bool): Whether to include comments in the archived document
            
        Returns:
            dict: The response from Reposis
        """
        # Create a PDF document
        pdf_buffer = ArchiveService.create_pdf(document_version, include_comments)
        
        # Get Reposis settings
        reposis_url = getattr(settings, 'REPOSIS_URL', '')
        reposis_username = getattr(settings, 'REPOSIS_USERNAME', '')
        reposis_password = getattr(settings, 'REPOSIS_PASSWORD', '')
        
        if not reposis_url or not reposis_username or not reposis_password:
            raise ValidationError("Reposis settings are not configured")
        
        # Prepare metadata
        metadata = {
            'title': document_version.publication.title,
            'abstract': document_version.technical_abstract,
            'doi': document_version.doi,
            'authors': [
                {
                    'name': author.name,
                    'institution': author.institution,
                    'orcid': author.orcid
                }
                for author in document_version.authors.all()
            ],
            'keywords': [
                keyword.keyword
                for keyword in document_version.keywords.all()
            ],
            'publication_date': document_version.release_date.isoformat() if document_version.release_date else None,
            'version': document_version.version_number,
        }
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_buffer.getvalue())
            temp_file_path = temp_file.name
        
        try:
            # Upload the document to Reposis
            files = {
                'file': ('document.pdf', open(temp_file_path, 'rb'), 'application/pdf')
            }
            
            response = requests.post(
                f"{reposis_url}/api/v1/documents",
                auth=(reposis_username, reposis_password),
                json=metadata,
                files=files
            )
            
            response.raise_for_status()
            
            # Get the response data
            response_data = response.json()
            
            # Update the document version with the Reposis ID
            document_version.metadata = document_version.metadata or {}
            document_version.metadata['reposis_id'] = response_data.get('id')
            document_version.save()
            
            return response_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error archiving document in Reposis: {e}")
            raise ValidationError(f"Error archiving document in Reposis: {e}")
        
        finally:
            # Delete the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)