Plea

# Living Science Documents – Gesamtkonzept

Dieses Dokument ist eine Zusammenfassung von Inhalten aus:
- ATT00001 (Fachliches Lastenheft),
- ATT00003 (Redaktions- und Workflowsystem),
- KI-Erweiterung Living Science Documents,
- sowie allen spezifizierten KI-Funktionen, Architekturaspekten, API-Schnittstellen und UI-Mockups aus der Gesprächen

Das Ziel: Ein dokumentierter, durchdachter und technisch ausführbarer Blueprint für eine kollaborative, versionierbare, wissenschaftlich betreute Veröffentlichungs- und Diskussionsplattform.

---

# 1. Einleitung

Living Science Documents (LSD) ist ein digitales System zur nachhaltigen Publikation, Diskussion und Weiterentwicklung wissenschaftlicher Arbeiten. Es basiert auf dem Konzept lebender Dokumente, die durch Versionierung, offene Kommentare und strukturierte Rollenprozesse kontinuierlich verbessert und ergänzt werden können.

Die Entwicklung des LSD erfolgt im Auftrag der **Leopoldina – Nationale Akademie der Wissenschaften** mit dem Ziel, die wissenschaftliche Qualitätssicherung in einer digitalen Umgebung zu stärken. Die Plattform setzt auf Transparenz, Nachvollziehbarkeit und partizipative Kommentierung – ergänzt durch moderne KI-Werkzeuge zur Kontextanalyse und Validitätssicherung.

### 1.1 Zielsetzung

- Etablierung eines digitalen, versionierten Publikationssystems
- Strukturierte Kommentierung und öffentliche Diskussion wissenschaftlicher Texte
- DOI-basierte Zitation von Haupttexten und Kommentaren
- Erweiterung um KI-basierte Analyse- und Unterstützungstools
- Unterstützung von Review- und Moderationsprozessen durch technische Hilfsmittel

### 1.2 Ursprung & Strukturierung

Dieses Dokument vereint:
- Das **Lastenheft** gemäß [ATT00001.docx]
- Das **Redaktions- und Ablaufkonzept** gemäß [ATT00003.docx]
- Die **technisch-funktionalen Erweiterungen** aus dem Dokument „KI-Erweiterung Living Science Documents“ und den begleitenden Fachdiskussionen (Chat-Protokolle, Architekturentscheidungen, UI-Mockups)

Alle Inhalte wurden überprüft, harmonisiert und auf Konsistenz geprüft. Die finale Struktur orientiert sich an den Anforderungen der redaktionellen Workflows und ergänzt diese durch technische Spezifikationselemente.

---
# 2. Organisation & Rollenmodell

Das Living Science Documents basiert auf einer klar definierten, mehrstufigen Rollenarchitektur, die sowohl wissenschaftliche Qualitätssicherung als auch technische Moderation sicherstellt. Die Rollen basieren auf dem Konzeptpapier der Leopoldina (ATT00001) und wurden um KI- und Systemfunktionen erweitert.

## 2.1 Organisationseinheiten

| Einheit          | Funktion / Ziel |
|------------------|------------------|
| **Leopoldina**   | Auftraggeber des Systems, gibt organisatorischen und finanziellen Rahmen sowie Projektziele vor. |
| **Betreiber**    | Technischer Systembetreiber (kann extern vergeben sein), verantwortlich für Hosting, Wartung, Sicherheit. |
| **Editorial Board** | Inhaltlich verantwortliches Fachgremium bestehend aus: Editorial Manager, Section Editors, Reviewing Editors, Editorial Office. Definiert redaktionelle Prozesse, Review-Standards und Kommentierregeln. |

## 2.2 Rollenübersicht

| Rolle             | Beschreibung |
|------------------|--------------|
| **Autor:in**       | Reicht Beiträge ein, reagiert auf Kommentare, hat keinen Einfluss auf Systemgestaltung. |
| **Kommentator:in** | Kann Abschnitte oder Kommentare kommentieren, benötigt Verifizierung. Kein Eingriff ins System. |
| **Leser:in**       | Findet und konsumiert Inhalte, benötigt kein Konto, kann aber keine Kommentare hinterlassen. |
| **Moderator:in**   | Sichtung, Prüfung und Freischaltung von Kommentaren. Zentrale Instanz für Qualitätskontrolle. |
| **Review Editor**  | Inhaltliche Prüfung und Zuordnung von Kommentaren. Schnittstelle zwischen Fachreview und Redaktion. |
| **Editorial Office** | Administrative Leitung, Definition der Abläufe, Freigabeprozesse, Rechtevergabe. |
| **Admin**          | Systemadministration, API-Zugänge, Modell- und Promptsteuerung, Sicherheit. |
| **KI-Assistenz (passiv)** | Unterstützt durch Vorschläge und Kontextanalysen, niemals autonom. Alle Vorschläge müssen freigegeben werden. |

## 2.3 Rechteverwaltung

Jede Rolle ist mit klaren Berechtigungen versehen. Eine Übersicht:

| Rolle               | Beiträge erstellen | Kommentieren | Kommentare prüfen | Versionen freigeben | KI-Konfiguration |
|---------------------|--------------------|--------------|--------------------|---------------------|------------------|
| Leser               | ❌                 | ❌           | ❌                 | ❌                  | ❌               |
| Kommentator         | ❌                 | ✅           | ❌                 | ❌                  | ❌               |
| Autor               | ✅                 | ✅ (nur bei eigenen Texten) | ❌        | ❌                  | ❌               |
| Moderator           | ❌                 | ✅           | ✅                 | ❌                  | ❌               |
| Review Editor       | ❌                 | ✅           | ✅                 | ✅                  | ❌               |
| Editorial Office    | ✅ (Admin)         | ✅           | ✅                 | ✅                  | ✅               |
| Admin               | ✅                 | ✅           | ✅                 | ✅                  | ✅               |

---

# 3. Einreichung, Begutachtung und Veröffentlichung

Der Veröffentlichungsprozess im Living Science Documents orientiert sich am eLife-Modell und wird ergänzt durch eine kommentierbare, versionierte Dokumentenlogik. Der Prozess ist in klar definierte Phasen unterteilt und erlaubt transparente Rückverfolgung jeder Entscheidung.

## 3.1 Einreichungsprozess

1. **Vorschlag oder Einladung** zur Einreichung
2. **Formatierte Erstversion** mit:
   - Technischem Abstract
   - Methodenteil (inkl. Literaturstrategie)
   - Haupttext inkl. Tabellen/Figuren
   - Autorenbeiträge, Interessenskonflikte
   - Funding und Danksagung
3. **Validierung durch Editorial Office**
   - Formale Prüfung
   - ORCID & Autorenprüfung
   - Metadaten-Anreicherung
4. **Zuweisung an Handling Editor**
   - Abschnittsspezifische Zuteilung
   - Definition der Reviewer

## 3.2 Begutachtung & Diskussion

- Zwei Reviews plus Kommentar des Editors
- Sichtung durch Reviewer mit Kommentarfunktion
- KI-Vorschläge (falls aktiv) nur zur Orientierung
- Moderierte Diskussion (intern)
- Zusammenfassung der Reviews → Empfehlung an Autor:in
- Kommentarveröffentlichung möglich (mit DOI)
- Erste offizielle Version: **v1.0**

## 3.3 Revisionsphase

- Autoren reichen überarbeitetes Dokument ein
- Ergänzt um:
   - Antwort auf Reviews (rSC-Format)
   - ggf. zusätzliche Daten (AD)
- Weitere Diskussion optional
- Finale Entscheidung durch Editorial Office + Senior Editor

## 3.4 Freigabe und Veröffentlichung

- Freigabe durch Editorial Office
- Publikation als „lebendes Dokument“
- Automatische DOI-Vergabe:
   - Hauptdokument
   - Alle freigegebenen Kommentare
   - Versionsnummer (v1.0, v1.1 etc.)

---

# 4. Struktur der Dokumente & Formatvorlagen

Das Living Science Documents arbeitet mit einer standardisierten Dokumentstruktur. Diese ermöglicht klare Zitation, Kommentierung, Abschnittsverlinkung und maschinenlesbare Weiterverarbeitung (z. B. durch KI oder Exporte nach JATS).

## 4.1 Gliederung wissenschaftlicher Beiträge

### Pflichtbestandteile

1. **Titel**
   - Kurzform (zitierfähig)
   - Langtitel
2. **Autor:innen**
   - Name, ORCID, Institution, Kontaktadresse
3. **Technical Abstract**
4. **Einleitung**
5. **Methodik**
6. **Haupttext**
   - Tabellen, Abbildungen, interaktive Inhalte möglich
7. **Fazit / Schlussfolgerungen**
8. **Autorenbeitrag & Interessenskonflikte**
9. **Danksagung & Fördermittel**
10. **Literaturverzeichnis**

### Optionale Elemente

- **Non-technical Abstract**
  - Für Laien verständlich, offen zugänglich, ggf. maschinell übersetzt
- **Schlagwörter**
- **Anhänge (Datasets, Scripts, Multimedia)**

## 4.2 Formatierungsvorgaben

- Strukturierung in nummerierte Abschnitte mit Zwischenüberschriften
- Abbildungen nummeriert und beschriftet
- Literatur im APA- oder Vancouver-Stil
- ORCID-Links als Pflichtfeld für Hauptautor:innen
- Zeilennummerierung zur Verlinkung von Kommentaren
- Alle Abschnitte einzeln versionierbar

## 4.3 Referenzierung und Zitation

- Jede Version des Dokuments erhält eine DOI
- Alle Kommentare mit DOI und Zitations

---

# 5. Kommentartypen und Kommentarsystem

Im LSD können verschiedene Arten von Kommentaren abgegeben werden. Jede Kommentarart hat ein standardisiertes Format, spezielle Anforderungen und wird im System unterschiedlich dargestellt.

## 5.1 Übersicht Kommentartypen

| Kürzel | Typ                  | Beschreibung                                               | DOI | Formatpflicht |
|--------|----------------------|------------------------------------------------------------|-----|--------------|
| SC     | Scientific Comment   | Fachlich-inhaltlicher Kommentar zu konkreten Textstellen   | Ja  | Ja           |
| rSC    | Response to SC       | Erwiderung auf einen SC                                    | Ja  | Ja           |
| ER     | Error Correction     | Korrektur sachlicher Fehler                                | Nein| Ja           |
| AD     | Additional Data      | Verweis auf ergänzende externe Daten oder Studien          | Ja  | Ja           |
| NP     | New Publication      | Hinweis auf eine neue relevante Publikation                | Ja  | Ja           |

## 5.2 Aufbau und Felder der Kommentare

Jeder Kommentar enthält:

- **Typ** (SC, rSC, ER, AD, NP)
- **Bezug** (Abschnitt, Zeilennummer oder Kommentarreferenz)
- **Autor:in** (Name, ORCID)
- **Datum der Einreichung**
- **Kommentartext** (nur in Frageform!)
- **Zitationsfeld** (bei Verweis auf Literatur)
- **DOI** (automatisch vergeben, außer bei ER)
- **Status** (neu, angenommen, abgelehnt inkl. Begründung)
- **Freigabedatum** (bei Veröffentlichung)

## 5.3 Anzeige und Verlinkung im Frontend

Kommentare werden seitlich des Dokuments angezeigt, verlinkt zur referenzierten Zeile oder zum Abschnitt.

╭────────── Scientific Comment (SC) ──────────╮
│ Bezug: Abschnitt 3, Zeile 112–145           │
│ Autor: Dr. Müller (ORCID: ...)              │
│ Eingereicht: 2025-04-13                     │
│ Typ: SC | DOI: 10.1234/repo.sc/2025.11      │
│                                             │
│ Text:                                       │
│ „Kann die Korrelation zwischen X und Y      │
│ nicht auch auf Methodik Z zurückzuführen     │
│ sein?“                                      │
╰─────────────────────────────────────────────╯

Kommentare sind durch Farbe und Label differenziert:

- Grün: Menschlich angenommen

- Hellgrün: KI-Kommentar angenommen

- Blau: Neuer menschlicher Kommentar

- Hellblau: Neuer KI-Kommentar

- Grau: Abgelehnt (mit Begründung)


## 5.4 Kommentarbegrenzung
KI-Kommentare: Maximal 10 pro Dokument, 1–2 pro Abschnitt

Menschliche Kommentare: Unbegrenzt, aber max. 2 pro Abschnitt und Tag (pro Nutzer:in)

Kommentare nur von verifizierten Nutzer:innen

## 5.5 DOI- und Zitierlogik
Alle SC, rSC, AD, NP erhalten eine eigene DOI und sind eigenständig zitierbar.

ER-Kommentare erhalten keine DOI, sind aber im Dokumentverlauf sichtbar.

Kommentare können in Literaturverzeichnisse exportiert werden.

## 5.6 Moderation und Freigabeprozess
Eingehende Kommentare landen zur Sichtung beim/bei der Moderator:in

Prüfung auf Formalia (Frageform, Quellenangabe, Bezug)

Freigabe oder Ablehnung mit Begründung

Bei Annahme: Sofortige Veröffentlichung, Zuweisung einer DOI

## 5.7 Timeline & Versionierung (Visualisierung)

[2025-03-01] Version 1.0 veröffentlicht
[2025-03-05] SC1 eingereicht (Dr. Müller)
[2025-03-07] SC1 freigeschaltet (Moderatorin XY)
[2025-03-10] rSC1.1 eingereicht (Autorenteam)
[2025-03-14] ER1 eingereicht
→ [2025-03-21] Version 1.1 veröffentlicht

---

# 6. Versionierung, Revisionshistorie und Timeline

Das Living Science Documents implementiert ein umfassendes, transparentes Versionsmanagement für Haupttexte und Kommentare. Jede Änderung ist nachvollziehbar, zitierbar und kann rückgängig gemacht werden.

## 6.1 Prinzipien der Versionierung

- Jede Änderung am Hauptdokument oder an Kommentaren erzeugt eine neue Version.
- Versionen sind fortlaufend nummeriert (v1.0, v1.1, v2.0, ...).
- Kommentare (außer ER) erhalten eigene DOIs, sind eigenständig referenzierbar und können ihrerseits kommentiert werden.
- Timeline: Chronologische Darstellung aller Einreichungen, Freigaben und Änderungen.
- Rücksprung auf jede frühere Version per Klick.

## 6.2 Detaillierte Ablaufbeispiele (Timeline / Mockup)

Beispiel-Zeitstrahl:
- 2025-04-01: v1.0 (Initiale Veröffentlichung)
- 2025-04-02: SC1 eingereicht (Bezug: Abschnitt 2)
- 2025-04-03: rSC1.1 (Antwort des Autorenteams)
- 2025-04-05: AD1 (Zusatzdaten von externer Forscher:in)
- 2025-04-06: NP1 (Verweis auf neue Publikation)
- → 2025-04-10: v1.1 (Eingepflegte Korrekturen/Antworten)
- 2025-05-01: v2.0 (Neuer Hauptautor, grundlegende Überarbeitung)

## 6.3 Anzeige und Navigation im Frontend

- Versionen und Kommentare sind über eine scrollbare Timeline zugänglich.
- Unterschiede zwischen Versionen werden farblich markiert (grün = hinzugefügt, rot = entfernt).
- Jeder Abschnitt kann einzeln in älteren Versionen angezeigt werden.
- Verlinkung zwischen Haupttext und Kommentaren (inkl. Sprungmarken zu Zeilennummern).

## 6.4 Rücksprung und Vergleich

- Nutzer:innen (mit entsprechender Rolle) können jede Version einzeln einsehen.
- Diff-Ansicht im Stil von GitHub: Vorher/Nachher mit Markierung aller Änderungen.
- Zurückrollen auf jede freigegebene Version durch das Editorial Office möglich.

## 6.5 Veröffentlichung neuer Versionen

- Nach Abschluss eines Review-/Kommentarlaufs erstellt das Editorial Office eine neue „Hauptversion“.
- Alle übernommenen Kommentare/Antworten werden automatisch mitveröffentlicht.
- Jede Hauptversion erhält eine eigene DOI und ist dauerhaft archiviert.

---

# 7. Redaktionelle Workflows, Rechte und Zuständigkeiten

Das Living Science Documents arbeitet nach klar definierten Prozessen und Workflows, die sich an internationalen Standards (u. a. eLife, PMC) orientieren und durch das Editorial Board der Leopoldina regelmäßig überprüft werden.

## 7.1 Überblick des Redaktionsworkflows

1. **Einreichung** des Manuskripts durch Autor:in
2. **Formale Prüfung** durch das Editorial Office
3. **Zuweisung** an Handling Editor und Reviewer
4. **Begutachtung** mit Kommentarfunktion (Review Editor, Reviewer, ggf. KI-Unterstützung)
5. **Moderation** der Kommentare durch Moderator:in
6. **Rückmeldung** an Autor:in mit ggf. Revision
7. **Freigabe** durch Editorial Office und Veröffentlichung als Version vX.X
8. **Offene Kommentierung** für verifizierte Nutzer:innen

## 7.2 Rechtevergabe und Zuständigkeiten

| Rolle               | Einreichen | Kommentieren | Freigeben | Moderieren | Versionieren | KI-Konfiguration |
|---------------------|------------|--------------|-----------|------------|--------------|------------------|
| Autor:in            | ✅         | Nur eigene   | ❌        | ❌         | ❌           | ❌               |
| Kommentator:in      | ❌         | ✅           | ❌        | ❌         | ❌           | ❌               |
| Moderator:in        | ❌         | ✅           | ✅        | ✅         | ❌           | ❌               |
| Review Editor       | ❌         | ✅           | ✅        | ✅         | ✅           | ❌               |
| Editorial Office    | ✅         | ✅           | ✅        | ✅         | ✅           | ✅               |
| Admin               | ✅         | ✅           | ✅        | ✅         | ✅           | ✅               |
| Betreiber           | (technisch) | ❌         | ❌        | ❌         | ❌           | ❌               |

## 7.3 Ablaufbeispiel (Flowchart-Text)

- Einreichung → Editorial Office (Prüfung)  
- ↳ Handling Editor (Zuteilung Reviewer)  
- ↳ Review-Phase (Kommentare SC, rSC, AD etc.)  
- ↳ Moderator:in prüft und gibt Kommentare frei  
- ↳ Autorenantwort (rSC)  
- ↳ Zusammenführung und Freigabe (Editorial Office)  
- ↳ Versionierung, DOI-Vergabe  
- ↳ Veröffentlichung + offene Kommentare

## 7.4 Besonderheiten

- **Alle Workflow-Schritte** sind dokumentiert, versioniert und per Timeline rückverfolgbar.
- **Jede Rolle** erhält nur die für sie vorgesehenen Rechte – Rechteeskalation nur durch Editorial Office oder Admin möglich.
- **Technische Betreiber** (z. B. externer Dienstleister) haben keinen Zugriff auf redaktionelle Inhalte.

---

# 8. Schnittstellen, APIs & technische Architektur

Das Living Science Documents setzt auf modulare, offene Schnittstellen und APIs zur Integration externer Datenquellen, Zitationsdienste und Validierungsdienste.

## 8.1 Systemarchitektur (High-Level)

- **Frontend**: React (mit Tailwind CSS), Markdown/HTML-Rendering
- **Backend**: Django (Python), RESTful API, Authentifizierung per OAuth2
- **Datenhaltung**: PostgreSQL (Metadaten), JATS-XML für Dokumentstruktur, Git-basierte Versionskontrolle
- **KI-Schnittstelle**: OpenAI GPT-4o (API via Proxy, konfigurierbar)
- **Kommentar- und Review-Engine**: Eigenes Modul, API-basiert
- **Externe APIs**:
  - Crossref (DOI- & Metadatenabfrage)
  - arXiv, Europe PMC (Volltext- & Metadatensuche)
  - ORCID (Autoren-Authentifizierung)
  - DataCite (DOI-Vergabe für Daten & Kommentare)
  - FundRef, Reposis (optional für Förderungs- und Archivierungsdienste)

## 8.2 API-Funktionen (Auswahl)

- **/documents/**  
  - GET: Abruf von Dokumenten mit Metadaten, Versionen, Kommentaren  
  - POST: Einreichen neuer Manuskripte  
  - PATCH/PUT: Überarbeiten/Versionieren  
  - DELETE: Entfernen (nur durch Editorial Office/Admin)

- **/comments/**  
  - GET: Liste/Feldsuche nach Kommentaren (Filter: Typ, Status, Abschnitt)  
  - POST: Kommentar einreichen (mit Bezug)  
  - PATCH: Kommentar bearbeiten/Status setzen  
  - DELETE: Kommentar zurückziehen

- **/users/**  
  - GET: Nutzersuche, Rollenabfrage  
  - POST: Registrierung, ORCID-Verknüpfung  
  - PATCH: Rollenwechsel (nur durch Editorial Office/Admin)

- **/review/**  
  - GET: Status aller laufenden Review-Prozesse  
  - POST: Review starten  
  - PATCH: Reviewer zuweisen, Status ändern

- **/ai/**  
  - POST: Kontextbasierter KI-Kommentarvorschlag (Rollen- & Promptlogik)

## 8.3 Schnittstellen zu Drittsystemen

- DOI-Resolver für Verlinkung und Import von Literatur
- ORCID für Autorenidentifikation und Autorisierung
- Export in JATS-XML, PDF/A für Archivierung in PubMed Central, Europe PMC etc.
- Optionale Integration von Plagiats- und Qualitäts-Checkern

## 8.4 Visualisierung der Systemarchitektur (ASCII-Mockup)

[Frontend (React)]
|
[Backend (Django REST)]
|
[PostgreSQL]---[JATS-Store]
|
[Kommentar-Modul]---[KI-API]
|
[Crossref/ORCID/arXiv/API]


## 8.5 Sicherheit & Logging

- OAuth2-Authentifizierung für alle Nutzer und Schnittstellen
- Rollenbasierte Zugriffskontrolle auf alle API-Endpunkte
- Vollständiges Logging aller API-Aufrufe und Datenänderungen (nachvollziehbar, DSGVO-konform)


---

# 9. KI-Funktionen & Logik

Das Living Science Documents integriert KI-basierte Unterstützung ausschließlich als passives, nachvollziehbares Assistenzsystem. KI darf keine Änderungen automatisch umsetzen – alle Vorschläge müssen durch Menschen geprüft und freigeschaltet werden.

## 9.1 Ziele der KI-Integration

- Unterstützung bei der Identifikation von Unsicherheiten, Inkonsistenzen und offenen Fragen in Manuskripten
- Kontextuelle Clusterung und Priorisierung von Kommentaren
- Vorschlag von Folgefragen oder alternativen Literaturhinweisen
- Semantische Verknüpfung ähnlicher Inhalte und automatisches Tagging

## 9.2 KI-Kommentare

- KI-Kommentare werden **ausschließlich in Frageform** formuliert (nie Behauptungen)
- Sie erscheinen visuell unterscheidbar (Label „KI-Vorschlag“, hellgrün)
- Max. 10 KI-Kommentare pro Dokument, 1–2 pro Abschnitt
- KI-Kommentare nur, wenn alle zugänglichen Quellen zur Verfügung stehen (Retrieval-Augmented Generation)
- KI muss für jede Aussage eine Quelle nennen (mit Titel, Autor, Datum, Vertrauenslevel)
- Prompt- und Antwort-Logs werden vollständig gespeichert (inkl. Version, Zeit, Nutzerrolle)
- Editorial Office entscheidet über Freischaltung/Veröffentlichung

## 9.3 Steuerung & Konfiguration

- KI-Modelle sind modular wählbar (OpenAI, lokale Modelle)
- Prompts können versioniert und angepasst werden (nur Editorial Office/Admin)
- Jedes KI-Feedback wird mit Input-Kontext und verwendeten Quellen im System dokumentiert
- Anpassbare Relevanzfilter (z. B. für Trust-Level, Aktualität, Themengebiet)

## 9.4 Vertrauensmodell bei KI-Kommentaren

- Vertrauenslevel jeder Quelle wird farblich und ikonografisch visualisiert:
  - Hoch = Peer-reviewed (🟢)
  - Mittel = Verifizierter Kommentar (🟡)
  - Niedrig = Externe Quelle ohne Review (🔴)
- Trust-Level beeinflusst Gewichtung in KI-Priorisierung und Sichtbarkeit
- Alle Zusammenfassungen werden im System gespeichert, Originalquellen nur verlinkt

## 9.5 Beispiel-Mockup: KI-Kommentar (Markdown)

---
**KI-Vorschlag (hellgrün, noch nicht freigegeben):**

*„Könnte die beobachtete Diskrepanz in Abschnitt 3 durch die in [Titel der Quelle] (Autor, Jahr) dargestellte Methodik erklärt werden?“*

Quelle: „Titel der Quelle“, Autor: Mustermann et al., 2024-02-03, Vertrauenslevel: Hoch (🟢)
---

## 9.6 Transparenz & Nachvollziehbarkeit

- KI-Vorschläge werden nie automatisch übernommen
- Jedes KI-Feedback ist versioniert, nachvollziehbar und revisionssicher archiviert
- Nutzer:innen können Feedback zu KI-Vorschlägen geben (Akzeptieren, Ablehnen, Kommentieren)

## 9.7 Grenzen & Anti-Halluzinations-Maßnahmen

- KI erhält nur zugelassene, geprüfte und zwischengespeicherte Kontexte
- Keine Annahmen oder „Fantasiequellen“ erlaubt
- Quellenprüfung durch Redaktion/KI vorgeschrieben
- Transparente Anzeige aller verwendeten Quellen und Prompts

---

# 10. Vertrauensmodell, Transparenz & Zitationslogik

Living Science Documents legt großen Wert auf Nachvollziehbarkeit und Vertrauenswürdigkeit aller Inhalte – sowohl für wissenschaftliche Publikationen als auch für KI-Vorschläge und Kommentare.

## 10.1 Vertrauenslevel

Jede Quelle, jeder Kommentar und jede Referenz wird mit einem **Vertrauenslevel** versehen, das systemweit sichtbar und filterbar ist.

- **Hoch:** Peer-Reviewte wissenschaftliche Artikel (🟢)
- **Mittel:** Kommentare von verifizierten Nutzer:innen (🟡)
- **Niedrig:** Externe Quellen ohne Peer-Review (🔴)

Diese Kennzeichnung wird an jeder Textstelle, in Zusammenfassungen, KI-Kommentaren und Verlinkungen dargestellt.

## 10.2 Visualisierung

- Farbliche Hervorhebung (Icons, Labels) in allen Ansichten und Filterlisten
- Separate Trust-Filter in Suchfunktion und Reviewer-Dashboards
- Trust-Level ist Bestandteil aller Metadatenexporte

## 10.3 Zitationslogik

- Jeder Beitrag, jede Version, jeder Kommentar (außer ER) erhält eine DOI (DataCite/Crossref)
- Zitation erfolgt nach gängigem wissenschaftlichen Standard (APA, Vancouver etc.)
- Export von Literatur- und Kommentarliste in Standardformaten (BibTeX, RIS)
- Kommentare und deren Erwiderungen sind zitierfähig und werden automatisch mit Quellverweis angezeigt

## 10.4 Quellenverlinkung und Zusammenfassungen

- Originalquellen werden ausschließlich **verlinkt** (kein Volltext im System)
- Zusammenfassungen (Abstract, Metadaten, Vertrauenslevel) werden gespeichert
- KI und Reviewer dürfen nur auf geprüfte, zwischengespeicherte Zusammenfassungen zugreifen

## 10.5 Kontrolle & Offenlegung

- Alle verwendeten Quellen werden für Nutzer:innen nachvollziehbar dargestellt
- Editorial Office und Reviewer haben spezielle Kontrollansichten zur Vertrauensbewertung
- Transparenzberichte zur Quellenbasis, KI-Kontext und Promptversionierung abrufbar

---

# 11. Datenhaltung, Export/Import & Archivierung

Das Living Science Repository setzt auf eine offene, interoperable Datenhaltung und bietet umfangreiche Export- und Archivierungsfunktionen für wissenschaftliche und technische Zwecke.

## 11.1 Datenstruktur

- Hauptdatenbank: PostgreSQL
- Langtexte, Versionen und Kommentare: JATS-XML-Struktur pro Dokument
- Metadaten: Autoren, ORCID, DOI, Funding, Trust-Level, Status, Workflow-Historie
- Alle Änderungen und Einreichungen sind vollständig versioniert und revisionssicher abgelegt

## 11.2 Exportformate

- JATS-XML: Standard für internationale Repositorien und Interoperabilität
- PDF/A: Archivierungsformat, inkl. aller Versionen und Kommentare
- HTML/Markdown: Für Webansicht und maschinelles Weiterverarbeiten
- BibTeX/RIS: Literatur- und Zitationsdatenbankexport

## 11.3 Importoptionen

- Manuskripte als Word, LaTeX oder PDF können importiert und in JATS-XML umgewandelt werden
- Automatisierte Feldzuordnung für Abstracts, Autoren, Referenzen, Abschnitte etc.
- Übernahme existierender DOIs, ORCID-IDs und Funding-Informationen

## 11.4 Archivierung & Dauerverfügbarkeit

- Alle Versionen, Kommentare und Metadaten werden langzeitarchiviert (min. 10 Jahre)
- Export zu PubMed Central, Europe PMC, institutional repositories via JATS
- DOI-Resolver für dauerhafte Zitierbarkeit
- Backup und DSGVO-konforme Aufbewahrung der Daten

## 11.5 Zugriffs- und Nutzungsrechte

- Öffentliche Zugänglichkeit für alle publizierten Inhalte (Open Access)
- Rollenbasierte Rechte für Kommentierung, Versionierung und Moderation
- Klare Lizenzangaben (CC BY, CC0 o. ä.) für alle veröffentlichten Inhalte

---

# 12. Governance, Qualitätssicherung & Weiterentwicklung

Das Living Science Repository unterliegt klaren Governance-Regeln und kontinuierlicher Qualitätssicherung, um wissenschaftliche Integrität, Transparenz und technische Nachhaltigkeit zu gewährleisten.

## 12.1 Governance-Struktur

- **Leopoldina** als inhaltlich und organisatorisch verantwortliche Institution
- **Editorial Board** mit Entscheidungsbefugnis für Prozesse, Workflows, Freigaben und Standards
- **Betreiber** (ggf. extern) für technischen Betrieb und Wartung
- **Regelmäßige Evaluation** der Abläufe, Tools und Nutzerfeedbacks

## 12.2 Qualitätssicherungsmaßnahmen

- Peer-Review für alle wissenschaftlichen Beiträge (zwingend für Erstveröffentlichung)
- Moderations- und Review-Protokolle mit Nachvollziehbarkeit aller Entscheidungen
- Automatisierte und manuelle Plagiats-Checks, Validitätsprüfungen, Quellenkontrolle
- KI-Feedback immer als Vorschlag, nie als automatisierte Änderung

## 12.3 Weiterentwicklung und Community-Beteiligung

- Dokumentierte Roadmap und Release-Zyklen
- Community-Calls und offene Workshops für Nutzerfeedback
- Offene Issues und Feature-Requests via GitHub-Integration
- Flexibler Ausbau von APIs, Datenmodellen und Frontend-Komponenten

## 12.4 Transparenz und Auditierbarkeit

- Offenlegung aller Workflows, Rechte, Review-Regeln und Prompt-Änderungen
- Veröffentlichung von Entscheidungslogs und Governance-Protokollen
- DSGVO-konforme Audit-Trails für alle personenbezogenen Daten

## 12.5 Notfallmanagement & Backup

- Notfallpläne für Datenverlust, Sicherheitsvorfälle, Systemausfälle
- Automatisierte Backups, regelmäßige Wiederherstellungstests
- Dokumentierte Eskalationswege für alle Organisations- und Betreiberrollen

---

# 13. Glossar, Anhänge & Mockups

## 13.1 Glossar zentraler Begriffe

- **LSD**: Living Science Documents – das Gesamtsystem für Publikation, Diskussion und Versionierung wissenschaftlicher Texte
- **DOI**: Digital Object Identifier – eindeutige Kennung für Publikationen, Kommentare, Versionen
- **JATS-XML**: Standardformat zur strukturierten Ablage wissenschaftlicher Artikel
- **Peer-Review**: Begutachtungsverfahren durch unabhängige Expert:innen
- **Editorial Board**: Gremium aus Editorial Manager, Section Editor, Reviewing Editor, Editorial Office
- **SC**: Scientific Comment
- **rSC**: Response to Scientific Comment
- **ER**: Error Correction
- **AD**: Additional Data
- **NP**: New Publication
- **Trust-Level**: Vertrauensniveau einer Quelle (hoch/mittel/niedrig)
- **KI**: Künstliche Intelligenz
- **ORCID**: Open Researcher and Contributor ID – eindeutige Autor:innen-Kennung

## 13.2 Beispiel-Mockups (ASCII-Text)

### Kommentarbox

### Beispiel: Kommentarbox (SC)

```
╭──────────── Scientific Comment (SC) ────────────╮
│ Bezug: Abschnitt 3, Zeile 120–130               │
│ Autor: Dr. Beispiel (ORCID: 0000-...)           │
│ Typ: SC | DOI: 10.1234/lsd.sc/2025.12           │
│ Status: Freigegeben (grün)                      │
│                                                 │
│ „Ist die Methodik in Abschnitt 3 konsistent      │
│ mit der in Publikation X beschriebenen?“         │
╰─────────────────────────────────────────────────╯
```

### Beispiel: Timeline-Versionsansicht

```
2025-03-01: v1.0 Initiale Veröffentlichung
2025-03-04: SC1 eingereicht
2025-03-06: rSC1.1 (Antwort Autor)
2025-03-07: AD1 (Zusatzdaten)
→ 2025-03-10: v1.1 Neue Hauptversion nach Revision
2025-04-01: v2.0 (Neuer Hauptautor, größere Überarbeitung)
```


### Beispiel: Systemarchitektur (ASCII)

```
[Frontend (React)]
      |
[Backend (Django REST)]
      |
[PostgreSQL]---[JATS-Store]
      |
 [Kommentar-Modul]---[KI-API]
      |
[Crossref/ORCID/arXiv/API]
```



