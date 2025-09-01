Section A: Research-Evidenz

- Thema: JATS Tag-Definitionen & Minimal-Subset (JATS 1.3)
  - Quelle: NISO JATS 1.3 Archiving and Interchange Tag Set (https://jats.nlm.nih.gov/archiving/tag-library/1.3/index.html) Stand: 2024-10
  - Kernaussage: JATS 1.3 definiert article/front/article-meta, body/sec, fig (graphic, caption, alt-text), back/ref-list. alt-text is allowed in fig; graphic uses xlink:href.
  - Relevanz: Bestätigt, dass unser Minimal-Subset mit sec, p, fig/graphic/caption/alt-text, ref-list, aff, contrib-meta valide ist.

- Thema: Unterschiede PMC/JATS 1.2/1.3
  - Quelle: PMC Tagging Guidelines (https://www.ncbi.nlm.nih.gov/pmc/pmcdoc/tagging-guidelines/) Stand: 2024-10
  - Kernaussage: PMC akzeptiert JATS Varianten, jedoch mit spezifischen Einschränkungen; unser MVP zielt auf generisches JATS 1.3 Subset, kompatibel zur späteren PMC-Anpassung.
  - Relevanz: MVP kann mit minimalem Subset starten; PMC-spezifika folgen.

- Thema: PDF/A Konformität & Engines
  - Quelle: WeasyPrint docs (https://doc.weasyprint.org/en/stable/api_reference.html#weasyprint.HTML.write_pdf) Stand: 2025-06
  - Kernaussage: write_pdf supports pdfa="2b" and fonts embedding; CSS-based rendering suitable for figures/captions.
  - Quelle: PDF/A overview (ISO 19005) summary (https://weasyprint.readthedocs.io/en/stable/features.html#pdf-a) Stand: 2025-06
  - Kernaussage: WeasyPrint can emit PDF/A-2b; requires embedded fonts.
  - Relevanz: WeasyPrint ist geeignet; ReportLab-Plain ist nicht PDF/A-konform out-of-the-box.

- Thema: Bibliografie-Formate & Mapping
  - Quelle: BibTeX entry guide (https://www.bibtex.com/g/bibtex-format/)
  - Quelle: RIS tags reference (https://en.wikipedia.org/wiki/RIS_(file_format)) Stand: 2024-10
  - Kernaussage: Minimalfelder (title, author, year, doi, url) sind ausreichend; RIS uses TY=JOUR, AU, TI, PY, DO, UR, VL.
  - Relevanz: Implementierte mappings in publications/citation.py decken dies ab.

Section B: Annahmen & Entscheidungen

- Entscheidung: Minimaler XSD für LSD-MVP statt vollständiger NISO XSDs; Begründung: geringe Komplexität, lokale Validierung in Tests. Alternative: Vendor der offiziellen JATS 1.3 RNG/XSD.
- Entscheidung: WeasyPrint als bevorzugter PDF/A-Renderer; Fallback ReportLab. Begründung: PDF/A-2b Support, CSS für Figuren/Caption. Alternative: XSL-FO (Apache FOP), höherer Integrationsaufwand.
- Entscheidung: Figures-Rendering in jats_to_html (figure/img/figcaption), damit HTML→PDF konsistent und stylingfähig ist.
- Entscheidung: Citation-Endpoints nutzen bestehende BibTeX/RIS Implementierung; Validierung via einfache Endpoint-Tests.
