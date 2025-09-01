# DOI Minting (DataCite) – Mapping & Examples

This document summarizes how the repository maps database fields to DataCite Metadata Schema for DOI minting when publishing a Document Version.

Scope (MVP): Only main document versions receive a DOI. Comments are excluded.

## Mapping DB → DataCite JSON

- attributes.doi ← DocumentVersion.doi
- attributes.titles[0].title ← Publication.title
- attributes.creators[] ← DocumentVersion.authors[]
  - name ← Author.name (fallback: user full name, username)
  - nameIdentifiers[0]
    - nameIdentifier ← ORCID as URL: https://orcid.org/{orcid}
    - nameIdentifierScheme ← "ORCID"
    - schemeUri ← "https://orcid.org"
  - affiliation[0].name ← Author.institution (if present)
- attributes.publisher ← settings.DATACITE_PUBLISHER (default: Leopoldina – ...)
- attributes.publicationYear ← DocumentVersion.release_date.year (fallback: current year)
- attributes.types.resourceTypeGeneral ← "Text"
- attributes.url (Landing Page) ← f"{FRONTEND_URL}/publication/{publication_id}?version={version_number}"
- attributes.relatedIdentifiers[ ] when Publication.meta_doi exists:
  - relationType ← "IsVersionOf"
  - relatedIdentifierType ← "DOI"
  - relatedIdentifier ← Publication.meta_doi

## Lifecycle

1) Create Draft DOI (idempotent)
- POST /dois with { data: { type: "dois", attributes: { doi } } }
- 201/200 ⇒ draft created; 409 ⇒ already exists (safe)

2) Update Metadata (PUT)
- PUT /dois/{doi} with full attributes from mapping above

3) Make Findable (Publish)
- PATCH /dois/{doi} with { data: { type: "dois", attributes: { event: "publish" } } }

4) Withdraw/Undo (Registered)
- PATCH /dois/{doi} with { data: { type: "dois", attributes: { event: "register" } } }

## Retry & Idempotency
- All DataCite calls use exponential backoff (0.5s, 1s, 2s) and X-Request-Id.
- publish action is idempotent: if already published with DOI state findable/registered, we return current data.

## Example Payloads

### Draft
{
  "data": {
    "type": "dois",
    "attributes": { "doi": "10.1234/lsd.document_version.42.1" }
  }
}

### Update (PUT)
{
  "data": {
    "type": "dois",
    "attributes": {
      "doi": "10.1234/lsd.document_version.42.1",
      "titles": [{"title": "Title of the Publication"}],
      "creators": [
        {
          "name": "Dr. Example",
          "nameIdentifiers": [
            {"nameIdentifier": "https://orcid.org/0000-0002-1825-0097", "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org"}
          ],
          "affiliation": [{"name": "University X"}]
        }
      ],
      "publisher": "Leopoldina – Nationale Akademie der Wissenschaften",
      "publicationYear": 2025,
      "types": {"resourceTypeGeneral": "Text"},
      "url": "https://example.org/publication/42?version=1",
      "relatedIdentifiers": [
        {"relationType": "IsVersionOf", "relatedIdentifierType": "DOI", "relatedIdentifier": "10.1234/lsd.publication.42"}
      ]
    }
  }
}

### Publish (Findable)
{
  "data": {"type": "dois", "attributes": {"event": "publish"}}
}

### Register (Withdraw/Undo)
{
  "data": {"type": "dois", "attributes": {"event": "register"}}
}

## Resolver & Landing Verification
Before making a DOI findable, we verify that the landing page URL returns HTTP 200 (with retries). After setting findable, we verify https://doi.org/{doi} returns 200/3xx (with retries). Warnings are logged if checks are not confirmed after retries.

## DB State
- DocumentVersion.doi (string, unique)
- DocumentVersion.doi_status ∈ { draft, registered, findable, error }

## Constraints & Policy (MVP)
- DOI only for main document versions (no comments)
- creators must be in question-form comments not relevant here; creators are actual authors for DOI metadata
- relatedIdentifiers uses IsVersionOf pointing to Publication.meta_doi
