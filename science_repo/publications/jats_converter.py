import logging
from lxml import etree
from io import StringIO
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class JATSConverter:
    """
    Utility class for converting between JATS-XML and other formats.
    Supports:
    - JATS-XML to HTML for display
    - Publication data to JATS-XML for export to repositories
    """

    @staticmethod
    def jats_to_html(jats_xml):
        """
        Convert JATS-XML to HTML for display.

        Args:
            jats_xml (str): JATS-XML content

        Returns:
            str: HTML content
        """
        if not jats_xml:
            return ""

        try:
            # Parse the JATS-XML
            parser = etree.XMLParser(recover=True)  # Use recover mode to handle malformed XML
            try:
                root = etree.fromstring(jats_xml.encode('utf-8'), parser)
            except Exception as e:
                logger.error(f"Error parsing JATS-XML: {str(e)}")
                # If parsing fails, try to clean the XML
                jats_xml = JATSConverter._clean_xml(jats_xml)
                root = etree.fromstring(jats_xml.encode('utf-8'), parser)

            # Create HTML output
            html = StringIO()
            html.write('<div class="jats-content">')

            # Process the article
            JATSConverter._process_article(root, html)

            html.write('</div>')
            return html.getvalue()

        except Exception as e:
            logger.error(f"Error converting JATS-XML to HTML: {str(e)}")
            # Return a simple error message wrapped in HTML
            return f'<div class="jats-error">Error converting document: {str(e)}</div>'

    @staticmethod
    def _clean_xml(xml_str):
        """Clean XML string to make it parseable."""
        # Remove any XML declaration
        xml_str = re.sub(r'<\?xml[^>]+\?>', '', xml_str)
        # Remove any DOCTYPE
        xml_str = re.sub(r'<!DOCTYPE[^>]+>', '', xml_str)
        # Replace any non-XML characters
        xml_str = re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]', '', xml_str)
        return xml_str

    @staticmethod
    def _process_article(article, html):
        """Process the article element and its children."""
        # Process front matter
        front = article.find('.//front')
        if front is not None:
            JATSConverter._process_front(front, html)

        # Process body
        body = article.find('.//body')
        if body is not None:
            JATSConverter._process_body(body, html)

        # Process back matter
        back = article.find('.//back')
        if back is not None:
            JATSConverter._process_back(back, html)

    @staticmethod
    def _process_front(front, html):
        """Process the front element (metadata, title, abstract, etc.)."""
        # Process article metadata
        article_meta = front.find('.//article-meta')
        if article_meta is not None:
            # Process title
            title_group = article_meta.find('.//title-group')
            if title_group is not None:
                article_title = title_group.find('.//article-title')
                if article_title is not None and article_title.text:
                    html.write(f'<h1 class="article-title">{article_title.text}</h1>')

            # Process authors
            contrib_group = article_meta.find('.//contrib-group')
            if contrib_group is not None:
                html.write('<div class="authors">')
                for contrib in contrib_group.findall('.//contrib'):
                    name = contrib.find('.//name')
                    if name is not None:
                        surname = name.find('.//surname')
                        given_names = name.find('.//given-names')
                        author_name = ""
                        if given_names is not None and given_names.text:
                            author_name += given_names.text + " "
                        if surname is not None and surname.text:
                            author_name += surname.text
                        if author_name:
                            html.write(f'<span class="author">{author_name}</span>')

                            # Add ORCID if available
                            contrib_id = contrib.find('.//contrib-id[@contrib-id-type="orcid"]')
                            if contrib_id is not None and contrib_id.text:
                                html.write(f' <span class="orcid">({contrib_id.text})</span>')

                            html.write(', ')
                html.write('</div>')

            # Process abstract
            abstract = article_meta.find('.//abstract')
            if abstract is not None:
                html.write('<div class="abstract"><h2>Abstract</h2>')
                for p in abstract.findall('.//p'):
                    if p.text:
                        html.write(f'<p>{p.text}</p>')
                html.write('</div>')

    @staticmethod
    def _process_body(body, html):
        """Process the body element (main content)."""
        html.write('<div class="body">')

        # Process sections
        for sec in body.findall('.//sec'):
            JATSConverter._process_section(sec, html)

        html.write('</div>')

    @staticmethod
    def _process_section(sec, html):
        """Process a section element."""
        # Get the section title
        title = sec.find('.//title')
        if title is not None and title.text:
            html.write(f'<h2 class="section-title">{title.text}</h2>')

        # Process paragraphs
        for p in sec.findall('.//p'):
            if p.text:
                html.write(f'<p>{p.text}</p>')

        # Process subsections recursively
        for subsec in sec.findall('.//sec'):
            JATSConverter._process_section(subsec, html)

    @staticmethod
    def _process_back(back, html):
        """Process the back element (references, appendices, etc.)."""
        html.write('<div class="back">')

        # Process references
        ref_list = back.find('.//ref-list')
        if ref_list is not None:
            html.write('<h2>References</h2><ol class="references">')
            for ref in ref_list.findall('.//ref'):
                mixed_citation = ref.find('.//mixed-citation')
                if mixed_citation is not None and mixed_citation.text:
                    html.write(f'<li>{mixed_citation.text}</li>')
            html.write('</ol>')

        html.write('</div>')

    @staticmethod
    def document_to_jats(document_version):
        """
        Convert a DocumentVersion to JATS-XML format for export to repositories.

        Args:
            document_version: The DocumentVersion object to convert

        Returns:
            str: JATS-XML content
        """
        try:
            # Create the root element
            root = etree.Element("article", 
                                attrib={
                                    "xmlns:xlink": "http://www.w3.org/1999/xlink",
                                    "xmlns:mml": "http://www.w3.org/1998/Math/MathML",
                                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                    "article-type": "research-article",
                                    "dtd-version": "1.3",
                                    "xml:lang": "en"
                                })

            # Create the front element (metadata)
            front = etree.SubElement(root, "front")

            # Journal metadata
            journal_meta = etree.SubElement(front, "journal-meta")
            journal_id = etree.SubElement(journal_meta, "journal-id", attrib={"journal-id-type": "publisher-id"})
            journal_id.text = "LSD"

            journal_title_group = etree.SubElement(journal_meta, "journal-title-group")
            journal_title = etree.SubElement(journal_title_group, "journal-title")
            journal_title.text = "Living Science Documents"

            issn = etree.SubElement(journal_meta, "issn", attrib={"pub-type": "epub"})
            issn.text = "XXXX-XXXX"  # Replace with actual ISSN if available

            publisher = etree.SubElement(journal_meta, "publisher")
            publisher_name = etree.SubElement(publisher, "publisher-name")
            publisher_name.text = "Leopoldina – Nationale Akademie der Wissenschaften"

            # Article metadata
            article_meta = etree.SubElement(front, "article-meta")

            # Article ID (DOI)
            article_id = etree.SubElement(article_meta, "article-id", attrib={"pub-id-type": "doi"})
            article_id.text = document_version.doi

            # Article categories
            if hasattr(document_version, 'keywords') and document_version.keywords.exists():
                article_categories = etree.SubElement(article_meta, "article-categories")
                subj_group = etree.SubElement(article_categories, "subj-group", attrib={"subj-group-type": "keywords"})
                for keyword in document_version.keywords.all():
                    subject = etree.SubElement(subj_group, "subject")
                    subject.text = keyword.name

            # Title group
            title_group = etree.SubElement(article_meta, "title-group")
            article_title = etree.SubElement(title_group, "article-title")
            article_title.text = document_version.publication.title

            if document_version.publication.short_title:
                alt_title = etree.SubElement(title_group, "alt-title", attrib={"alt-title-type": "short"})
                alt_title.text = document_version.publication.short_title

            # Contributors (authors)
            contrib_group = etree.SubElement(article_meta, "contrib-group")
            for author in document_version.authors.all().order_by('order'):
                contrib = etree.SubElement(contrib_group, "contrib", attrib={"contrib-type": "author"})

                # Name
                name = etree.SubElement(contrib, "name")
                # Assuming name is in format "First Last"
                name_parts = author.name.split(' ', 1)
                if len(name_parts) > 1:
                    given_names = etree.SubElement(name, "given-names")
                    given_names.text = name_parts[0]
                    surname = etree.SubElement(name, "surname")
                    surname.text = name_parts[1]
                else:
                    surname = etree.SubElement(name, "surname")
                    surname.text = author.name

                # ORCID
                if author.orcid:
                    contrib_id = etree.SubElement(contrib, "contrib-id", attrib={"contrib-id-type": "orcid"})
                    contrib_id.text = author.orcid

                # Affiliation
                if author.institution:
                    aff = etree.SubElement(contrib, "aff")
                    institution = etree.SubElement(aff, "institution")
                    institution.text = author.institution

                    if author.address:
                        addr = etree.SubElement(aff, "addr-line")
                        addr.text = author.address

                # Corresponding author
                if author.is_corresponding:
                    xref = etree.SubElement(contrib, "xref", attrib={"ref-type": "corresp", "rid": "cor1"})

            # Publication date
            pub_date = etree.SubElement(article_meta, "pub-date", attrib={"pub-type": "epub"})

            release_date = document_version.release_date or document_version.status_date.date()
            day = etree.SubElement(pub_date, "day")
            day.text = str(release_date.day)
            month = etree.SubElement(pub_date, "month")
            month.text = str(release_date.month)
            year = etree.SubElement(pub_date, "year")
            year.text = str(release_date.year)

            # Version
            version = etree.SubElement(article_meta, "version")
            version.text = str(document_version.version_number)

            # Abstract
            if document_version.technical_abstract:
                abstract = etree.SubElement(article_meta, "abstract")
                p = etree.SubElement(abstract, "p")
                p.text = document_version.technical_abstract

            if document_version.non_technical_abstract:
                abstract = etree.SubElement(article_meta, "abstract", attrib={"abstract-type": "non-technical"})
                p = etree.SubElement(abstract, "p")
                p.text = document_version.non_technical_abstract

            # Funding
            if document_version.funding:
                funding_group = etree.SubElement(article_meta, "funding-group")
                funding_statement = etree.SubElement(funding_group, "funding-statement")
                funding_statement.text = document_version.funding

            # Body
            body = etree.SubElement(root, "body")

            # Introduction
            if document_version.introduction:
                sec = etree.SubElement(body, "sec", attrib={"sec-type": "intro"})
                title = etree.SubElement(sec, "title")
                title.text = "Introduction"
                p = etree.SubElement(sec, "p")
                p.text = document_version.introduction

            # Methodology
            if document_version.methodology:
                sec = etree.SubElement(body, "sec", attrib={"sec-type": "methods"})
                title = etree.SubElement(sec, "title")
                title.text = "Methodology"
                p = etree.SubElement(sec, "p")
                p.text = document_version.methodology

            # Main text
            if document_version.main_text:
                sec = etree.SubElement(body, "sec", attrib={"sec-type": "results"})
                title = etree.SubElement(sec, "title")
                title.text = "Results"
                p = etree.SubElement(sec, "p")
                p.text = document_version.main_text

            # Conclusion
            if document_version.conclusion:
                sec = etree.SubElement(body, "sec", attrib={"sec-type": "conclusion"})
                title = etree.SubElement(sec, "title")
                title.text = "Conclusion"
                p = etree.SubElement(sec, "p")
                p.text = document_version.conclusion

            # Back matter
            back = etree.SubElement(root, "back")

            # Acknowledgments
            if document_version.acknowledgments:
                ack = etree.SubElement(back, "ack")
                title = etree.SubElement(ack, "title")
                title.text = "Acknowledgments"
                p = etree.SubElement(ack, "p")
                p.text = document_version.acknowledgments

            # Author contributions
            if document_version.author_contributions:
                sec = etree.SubElement(back, "sec", attrib={"sec-type": "author-contributions"})
                title = etree.SubElement(sec, "title")
                title.text = "Author Contributions"
                p = etree.SubElement(sec, "p")
                p.text = document_version.author_contributions

            # Conflicts of interest
            if document_version.conflicts_of_interest:
                sec = etree.SubElement(back, "sec", attrib={"sec-type": "conflicts"})
                title = etree.SubElement(sec, "title")
                title.text = "Conflicts of Interest"
                p = etree.SubElement(sec, "p")
                p.text = document_version.conflicts_of_interest

            # References
            if document_version.references:
                ref_list = etree.SubElement(back, "ref-list")
                title = etree.SubElement(ref_list, "title")
                title.text = "References"

                # Simple parsing of references (one per line)
                for i, ref_text in enumerate(document_version.references.strip().split('\n'), 1):
                    if ref_text.strip():
                        ref = etree.SubElement(ref_list, "ref", attrib={"id": f"ref{i}"})
                        mixed_citation = etree.SubElement(ref, "mixed-citation")
                        mixed_citation.text = ref_text.strip()

            # Convert to string
            return etree.tostring(root, pretty_print=True, encoding='utf-8').decode('utf-8')

        except Exception as e:
            logger.error(f"Error converting document to JATS-XML: {str(e)}")
            raise ValueError(f"Error converting document to JATS-XML: {str(e)}")
