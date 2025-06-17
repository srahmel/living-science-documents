# Export Functionality for Living Science Documents

This document describes the export functionality available in the Living Science Documents platform, including JATS-XML export for submission to repositories like PubMed Central, Europe PMC, and institutional repositories.

## Available Export Formats

### JATS-XML

JATS (Journal Article Tag Suite) is an XML format used for archiving and exchanging journal articles. It is the standard format required by PubMed Central, Europe PMC, and many institutional repositories.

The JATS-XML export includes:
- Publication metadata (title, authors, DOI, etc.)
- Abstract (technical and non-technical)
- Full text content (introduction, methodology, main text, conclusion)
- References
- Funding information
- Author contributions and conflicts of interest

### PDF

PDF export creates a PDF/A document from a document version, optionally including comments.

## API Endpoints

### Export to JATS-XML

```
GET /api/publications/document-versions/{id}/jats/
```

**Parameters:**
- `id` (path parameter): The ID of the document version to export

**Response:**
- JATS-XML file as an attachment

**Example:**
```
GET /api/publications/document-versions/123/jats/
```

### Export to Repository

```
GET /api/publications/document-versions/{id}/repository/
```

**Parameters:**
- `id` (path parameter): The ID of the document version to export
- `repository` (query parameter): The repository to export to. Options:
  - `pubmed`: PubMed Central
  - `europepmc`: Europe PMC
  - `institutional`: Institutional repository

**Response:**
- JSON object with export status and repository information

**Example:**
```
GET /api/publications/document-versions/123/repository/?repository=pubmed
```

### Download PDF

```
GET /api/publications/document-versions/{id}/pdf/
```

**Parameters:**
- `id` (path parameter): The ID of the document version to export
- `include_comments` (query parameter, optional): Whether to include comments in the PDF (default: true)

**Response:**
- PDF file as an attachment

**Example:**
```
GET /api/publications/document-versions/123/pdf/?include_comments=false
```

## Repository Submission Guidelines

### PubMed Central

PubMed Central (PMC) is a free full-text archive of biomedical and life sciences journal literature at the U.S. National Institutes of Health's National Library of Medicine (NIH/NLM).

To submit to PMC:
1. Export your document to JATS-XML format
2. Visit the [PMC Publisher Portal](https://www.ncbi.nlm.nih.gov/pmc/publish/)
3. Follow the submission guidelines

### Europe PMC

Europe PMC is a repository of life sciences literature, including articles, books, patents, and clinical guidelines.

To submit to Europe PMC:
1. Export your document to JATS-XML format
2. Visit the [Europe PMC Plus submission system](https://plus.europepmc.org/)
3. Follow the submission guidelines

### Institutional Repositories

Many institutional repositories accept JATS-XML format for submission. The specific submission process will depend on your institution's repository system.

## JATS-XML Format Details

The JATS-XML export follows the JATS 1.3 DTD standard and includes the following elements:

- `<article>`: Root element
- `<front>`: Front matter (metadata)
  - `<journal-meta>`: Journal metadata
  - `<article-meta>`: Article metadata (title, authors, abstract, etc.)
- `<body>`: Main content
  - `<sec>`: Sections (introduction, methodology, results, conclusion)
- `<back>`: Back matter
  - `<ref-list>`: References
  - `<ack>`: Acknowledgments

For more details on the JATS format, see the [JATS Documentation](https://jats.nlm.nih.gov/archiving/).