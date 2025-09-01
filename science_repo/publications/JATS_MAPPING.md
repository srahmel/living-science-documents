# JATS Minimal Subset Mapping (PM JSON ↔ JATS)

This document maps the internal Publication/DocumentVersion (PM JSON) fields to the JATS-XML minimal subset used by LSD MVP.

Schema reference: publications/schemas/lsd-jats-minimal.xsd (based on JATS 1.3 elements; limited to subset: sec, p, fig/graphic, caption, alt-text, ref-list, aff, contrib-meta).

- publication.title → /article/front/article-meta/title-group/article-title
- publication.short_title → /article/front/article-meta/title-group/alt-title[@alt-title-type="short"]
- document_version.doi → /article/front/article-meta/article-id[@pub-id-type="doi"]
- authors (Author model) → /article/front/article-meta/contrib-group/contrib[@contrib-type="author"]
  - Author.name (split) → name/given-names, name/surname
  - Author.orcid → contrib-id[@contrib-id-type="orcid"]
  - Author.institution → aff/institution
  - Author.address → aff/addr-line
  - Author.is_corresponding → xref[@ref-type="corresp"]
- release_date or status_date → /article/front/article-meta/pub-date[@pub-type="epub"]/day|month|year
- version_number → /article/front/article-meta/version
- technical_abstract → /article/front/article-meta/abstract/p
- non_technical_abstract → /article/front/article-meta/abstract[@abstract-type="non-technical"]/p
- funding → /article/front/article-meta/funding-group/funding-statement
- introduction → /article/body/sec[@sec-type="intro"]/title + p
- methodology → /article/body/sec[@sec-type="methods"]/title + p
- main_text → /article/body/sec[@sec-type="results"]/title + p
- conclusion → /article/body/sec[@sec-type="conclusion"]/title + p
- figures (Figure model) → /article/body/sec[@sec-type="figures"]/fig
  - Figure.caption → fig/caption/p
  - Figure.alt_text → fig/alt-text
  - Figure.image (URL) → fig/graphic[@xlink:href]
  - Optional: license/source/attribution → data-* attributes on fig
- acknowledgments → /article/back/ack/title + p
- author_contributions → /article/back/sec[@sec-type="author-contributions"]/title + p
- conflicts_of_interest → /article/back/sec[@sec-type="conflicts"]/title + p
- references (single string, 1 per line) → /article/back/ref-list/ref/mixed-citation

Notes:
- Names are split on first space: “First Last”. Improve later for multi-part names.
- Graphics use xlink:href with xmlns:xlink declared on root.
- XML attributes on root include article-type="research-article", dtd-version="1.3", xml:lang="en".

Validation:
- Minimal subset XSD: publications/schemas/lsd-jats-minimal.xsd (validated in test_jats_minimal_validation.py)
- For full JATS 1.3 conformance, integrate official NISO JATS 1.3 schemas; out of scope for MVP.
