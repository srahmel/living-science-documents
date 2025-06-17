# Document Import Feature

This document explains how to use the document import feature in the Living Science Documents platform.

## Overview

The Living Science Documents platform allows you to import documents in various formats (Word, LaTeX, PDF) and automatically convert them to JATS-XML and HTML for display. This feature makes it easy to create new documents or update existing ones by uploading files you already have.

## Supported File Formats

The following file formats are supported:
- Microsoft Word (.docx, .doc)
- LaTeX (.tex, .latex)
- PDF (.pdf)

## How to Import a Document

### When Creating a New Document

1. Create a new publication through the API or user interface
2. Once the publication is created, a draft document version is automatically created
3. Use the import endpoint to upload your document file:

```
POST /api/import-document/{document_version_id}/
```

Replace `{document_version_id}` with the ID of the document version you want to update.

### Importing Without a Document Version

You can also import a document without specifying a document version:

```
POST /api/import-document/
```

This will extract the content and metadata from the document but won't save it to any document version. The response will contain the extracted content, which you can then use to create a new document version.

## API Endpoints

### Import Document

```
POST /api/import-document/
```

**Parameters:**
- `file`: The document file to import (multipart/form-data)

**Response:**
```json
{
  "title": "Document Title",
  "abstract": "Document Abstract",
  "authors": ["Author 1", "Author 2"],
  "doi": "10.1234/example",
  "orcid_ids": ["0000-0001-2345-6789"],
  "funding_info": "Funding information",
  "jats_xml": "<article>...</article>",
  "sections": [
    {
      "title": "Introduction",
      "content": ["Paragraph 1", "Paragraph 2"]
    },
    {
      "title": "Methods",
      "content": ["Paragraph 1", "Paragraph 2"]
    }
  ],
  "references": ["Reference 1", "Reference 2"]
}
```

### Import Document to Existing Version

```
POST /api/document-versions/{document_version_id}/import/
```

**Parameters:**
- `document_version_id`: The ID of the document version to update
- `file`: The document file to import (multipart/form-data)

**Response:**
```json
{
  "id": 1,
  "publication": 1,
  "version_number": 1,
  "doi": "10.1234/example.1",
  "content": "<article>...</article>",
  "html_content": "<div class=\"jats-content\">...</div>",
  "title": "Document Title",
  "abstract": "Document Abstract",
  "authors": [
    {
      "id": 1,
      "name": "Author 1",
      "orcid": "0000-0001-2345-6789"
    }
  ],
  "status": "draft"
}
```

## Automatic Field Mapping

When importing a document, the system automatically extracts and maps the following fields:
- Title
- Abstract
- Authors
- DOI
- ORCID IDs
- Funding information
- Sections (Introduction, Methods, Results, etc.)
- References

## HTML Conversion

The imported document is automatically converted to HTML for display. The HTML content is stored in the `html_content` field of the document version and can be used to display the document in a web browser.

## Example Usage

Here's an example of how to import a document using cURL:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/your/document.docx" \
  http://localhost:8000/api/document-versions/1/import/
```

## Troubleshooting

If you encounter any issues when importing a document, check the following:
- Make sure the file format is supported
- Check that the file is not corrupted
- Ensure that you have the necessary permissions to update the document version
- If the document is not being parsed correctly, try a different file format