import requests
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
import os
import tempfile
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

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
        elements.append(Paragraph("Technical Abstract", styles['Heading2']))
        elements.append(Paragraph(document_version.technical_abstract, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add introduction
        elements.append(Paragraph("Introduction", styles['Heading2']))
        elements.append(Paragraph(document_version.introduction, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add methodology
        elements.append(Paragraph("Methodology", styles['Heading2']))
        elements.append(Paragraph(document_version.methodology, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add main text
        elements.append(Paragraph("Main Text", styles['Heading2']))
        elements.append(Paragraph(document_version.main_text, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add conclusion
        elements.append(Paragraph("Conclusion", styles['Heading2']))
        elements.append(Paragraph(document_version.conclusion, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add author contributions
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