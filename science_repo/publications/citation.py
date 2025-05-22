import os
import tempfile
from django.conf import settings
import logging
import json
import re

logger = logging.getLogger(__name__)


class CitationService:
    """
    Service for generating citation formats for publications and comments.
    
    This service provides methods for:
    - Generating citations in various formats (BibTeX, RIS, etc.)
    - Generating citations in various styles (APA, MLA, Chicago, etc.)
    """
    
    @staticmethod
    def generate_bibtex(document_version):
        """
        Generate a BibTeX citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            
        Returns:
            str: The BibTeX citation
        """
        # Get the authors
        authors = document_version.authors.all()
        author_names = []
        for author in authors:
            if author.name:
                # Split the name into first and last name
                name_parts = author.name.split()
                if len(name_parts) > 1:
                    last_name = name_parts[-1]
                    first_name = ' '.join(name_parts[:-1])
                    author_names.append(f"{last_name}, {first_name}")
                else:
                    author_names.append(author.name)
        
        # Create a BibTeX key from the first author's last name and the year
        first_author = authors.first()
        if first_author and first_author.name:
            name_parts = first_author.name.split()
            if len(name_parts) > 1:
                first_author_last_name = name_parts[-1]
            else:
                first_author_last_name = first_author.name
        else:
            first_author_last_name = "Unknown"
        
        year = document_version.release_date.year if document_version.release_date else "Unknown"
        bibtex_key = f"{first_author_last_name}{year}"
        
        # Generate the BibTeX citation
        bibtex = f"@article{{{bibtex_key},\n"
        bibtex += f"  title = {{{document_version.publication.title}}},\n"
        bibtex += f"  author = {{{' and '.join(author_names)}}},\n"
        
        if document_version.release_date:
            bibtex += f"  year = {{{document_version.release_date.year}}},\n"
            bibtex += f"  month = {{{document_version.release_date.month}}},\n"
        
        bibtex += f"  doi = {{{document_version.doi}}},\n"
        bibtex += f"  url = {{https://doi.org/{document_version.doi}}},\n"
        bibtex += f"  version = {{{document_version.version_number}}},\n"
        
        # Add abstract if available
        if document_version.technical_abstract:
            bibtex += f"  abstract = {{{document_version.technical_abstract}}},\n"
        
        # Add keywords if available
        keywords = document_version.keywords.all()
        if keywords.exists():
            keyword_list = [keyword.keyword for keyword in keywords]
            bibtex += f"  keywords = {{{', '.join(keyword_list)}}},\n"
        
        # Remove the trailing comma and newline
        bibtex = bibtex.rstrip(",\n") + "\n"
        
        bibtex += "}"
        
        return bibtex
    
    @staticmethod
    def generate_ris(document_version):
        """
        Generate a RIS citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            
        Returns:
            str: The RIS citation
        """
        # Start the RIS citation
        ris = "TY  - JOUR\n"  # Type: Journal article
        
        # Add the title
        ris += f"TI  - {document_version.publication.title}\n"
        
        # Add the authors
        for author in document_version.authors.all():
            if author.name:
                # Split the name into first and last name
                name_parts = author.name.split()
                if len(name_parts) > 1:
                    last_name = name_parts[-1]
                    first_name = ' '.join(name_parts[:-1])
                    ris += f"AU  - {last_name}, {first_name}\n"
                else:
                    ris += f"AU  - {author.name}\n"
        
        # Add the publication date
        if document_version.release_date:
            ris += f"PY  - {document_version.release_date.year}\n"
            ris += f"DA  - {document_version.release_date.year}/{document_version.release_date.month}/{document_version.release_date.day}\n"
        
        # Add the DOI
        ris += f"DO  - {document_version.doi}\n"
        
        # Add the URL
        ris += f"UR  - https://doi.org/{document_version.doi}\n"
        
        # Add the version
        ris += f"VL  - {document_version.version_number}\n"
        
        # Add the abstract if available
        if document_version.technical_abstract:
            ris += f"AB  - {document_version.technical_abstract}\n"
        
        # Add keywords if available
        for keyword in document_version.keywords.all():
            ris += f"KW  - {keyword.keyword}\n"
        
        # End the RIS citation
        ris += "ER  - \n"
        
        return ris
    
    @staticmethod
    def generate_citation(document_version, format_type, citation_style=None):
        """
        Generate a citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            format_type (str): The format type ('bibtex', 'ris', 'text')
            citation_style (str, optional): The citation style for text format
                                          ('apa', 'mla', 'chicago', etc.)
            
        Returns:
            str: The citation
        """
        if format_type == 'bibtex':
            return CitationService.generate_bibtex(document_version)
        elif format_type == 'ris':
            return CitationService.generate_ris(document_version)
        elif format_type == 'text':
            # For text format, we need a citation style
            if not citation_style:
                citation_style = 'apa'  # Default to APA style
            
            # Generate the text citation based on the style
            if citation_style == 'apa':
                return CitationService.generate_apa_citation(document_version)
            elif citation_style == 'mla':
                return CitationService.generate_mla_citation(document_version)
            elif citation_style == 'chicago':
                return CitationService.generate_chicago_citation(document_version)
            else:
                raise ValueError(f"Unsupported citation style: {citation_style}")
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    @staticmethod
    def generate_apa_citation(document_version):
        """
        Generate an APA style citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            
        Returns:
            str: The APA style citation
        """
        # Get the authors
        authors = document_version.authors.all()
        author_names = []
        for author in authors:
            if author.name:
                # Split the name into first and last name
                name_parts = author.name.split()
                if len(name_parts) > 1:
                    last_name = name_parts[-1]
                    first_name = ' '.join(name_parts[:-1])
                    # Format as "Last, F."
                    first_initial = first_name[0] if first_name else ""
                    author_names.append(f"{last_name}, {first_initial}.")
                else:
                    author_names.append(author.name)
        
        # Format the authors
        if len(author_names) == 1:
            authors_text = author_names[0]
        elif len(author_names) == 2:
            authors_text = f"{author_names[0]} & {author_names[1]}"
        elif len(author_names) > 2:
            authors_text = ", ".join(author_names[:-1]) + f", & {author_names[-1]}"
        else:
            authors_text = "Unknown"
        
        # Format the year
        year = document_version.release_date.year if document_version.release_date else "n.d."
        
        # Format the title (in italics, but we can't do that in plain text)
        title = document_version.publication.title
        
        # Format the DOI
        doi = document_version.doi
        
        # Generate the APA citation
        citation = f"{authors_text} ({year}). {title}. https://doi.org/{doi}"
        
        return citation
    
    @staticmethod
    def generate_mla_citation(document_version):
        """
        Generate an MLA style citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            
        Returns:
            str: The MLA style citation
        """
        # Get the authors
        authors = document_version.authors.all()
        author_names = []
        for author in authors:
            if author.name:
                # Split the name into first and last name
                name_parts = author.name.split()
                if len(name_parts) > 1:
                    last_name = name_parts[-1]
                    first_name = ' '.join(name_parts[:-1])
                    author_names.append(f"{last_name}, {first_name}")
                else:
                    author_names.append(author.name)
        
        # Format the authors
        if len(author_names) == 1:
            authors_text = author_names[0]
        elif len(author_names) == 2:
            authors_text = f"{author_names[0]} and {author_names[1]}"
        elif len(author_names) > 2:
            authors_text = author_names[0] + ", et al."
        else:
            authors_text = "Unknown"
        
        # Format the title (in quotes)
        title = f'"{document_version.publication.title}"'
        
        # Format the date
        if document_version.release_date:
            date = document_version.release_date.strftime("%d %b. %Y")
        else:
            date = "n.d."
        
        # Format the DOI
        doi = document_version.doi
        
        # Generate the MLA citation
        citation = f"{authors_text}. {title}. {date}, https://doi.org/{doi}."
        
        return citation
    
    @staticmethod
    def generate_chicago_citation(document_version):
        """
        Generate a Chicago style citation for a document version.
        
        Args:
            document_version: The document version to generate a citation for
            
        Returns:
            str: The Chicago style citation
        """
        # Get the authors
        authors = document_version.authors.all()
        author_names = []
        for author in authors:
            if author.name:
                # Split the name into first and last name
                name_parts = author.name.split()
                if len(name_parts) > 1:
                    last_name = name_parts[-1]
                    first_name = ' '.join(name_parts[:-1])
                    author_names.append(f"{last_name}, {first_name}")
                else:
                    author_names.append(author.name)
        
        # Format the authors
        if len(author_names) == 1:
            authors_text = author_names[0]
        elif len(author_names) == 2:
            authors_text = f"{author_names[0]} and {author_names[1]}"
        elif len(author_names) > 2:
            authors_text = ", ".join(author_names[:-1]) + f", and {author_names[-1]}"
        else:
            authors_text = "Unknown"
        
        # Format the title (in quotes)
        title = f'"{document_version.publication.title}"'
        
        # Format the date
        if document_version.release_date:
            date = document_version.release_date.strftime("%B %d, %Y")
        else:
            date = "n.d."
        
        # Format the DOI
        doi = document_version.doi
        
        # Generate the Chicago citation
        citation = f"{authors_text}. {title}. {date}. https://doi.org/{doi}."
        
        return citation
    
    @staticmethod
    def get_available_citation_styles():
        """
        Get a list of available citation styles.
        
        Returns:
            list: A list of available citation styles
        """
        return [
            {'id': 'apa', 'name': 'APA (American Psychological Association)'},
            {'id': 'mla', 'name': 'MLA (Modern Language Association)'},
            {'id': 'chicago', 'name': 'Chicago'},
        ]
    
    @staticmethod
    def get_available_citation_formats():
        """
        Get a list of available citation formats.
        
        Returns:
            list: A list of available citation formats
        """
        return [
            {'id': 'bibtex', 'name': 'BibTeX', 'extension': 'bib'},
            {'id': 'ris', 'name': 'RIS (Research Information Systems)', 'extension': 'ris'},
            {'id': 'text', 'name': 'Plain Text', 'extension': 'txt'},
        ]