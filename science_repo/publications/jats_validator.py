from lxml import etree
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schemas', 'lsd-jats-minimal.xsd')


def validate_minimal_jats(jats_xml: str) -> None:
    """
    Validate JATS-XML against the LSD minimal JATS subset schema.

    Raises etree.DocumentInvalid if the XML does not conform.
    """
    if not jats_xml:
        raise ValueError("Empty JATS-XML provided for validation")
    parser = etree.XMLParser(remove_blank_text=True)
    doc = etree.fromstring(jats_xml.encode('utf-8'), parser)
    with open(SCHEMA_PATH, 'rb') as f:
        schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)
    schema.assertValid(doc)
