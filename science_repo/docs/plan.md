# Living Science Documents – Project Improvement Plan

Last updated: 2025-08-22 11:55 (local)

Sources considered:
- .junie/guidelines.md (Gesamtkonzept, provided in full)
- docs/requirements.md (not found in repository at time of writing; see Risks & Open Questions)

Scope: This plan extracts key goals and constraints and proposes concrete, rationale-backed improvements across backend (Django REST), data model (PostgreSQL + JATS-XML), APIs, moderation/review workflows, AI assist features, security/compliance, and frontend UX. It is designed to be actionable in iterative phases without destabilizing the existing codebase.

---

## 1. Key Goals (from guidelines)
- Establish a digital, versioned publication system with transparent, citable versions (1.1; 6.x).
- Structured commenting and public discussion with moderation and DOI-based citation of comments (3.x; 5.x; 10.3).
- Clear role model and RBAC across the platform (2.x; 7.x; 8.5).
- AI as passive assistant only: question-form suggestions, source-backed (RAG), rate-limited, fully logged (9.x).
- Trust/transparency model, auditability, and export capabilities (10.x; 11.x; 12.x).

## 2. Core Constraints & Principles
- Human-in-the-loop: No autonomous KI actions; all suggestions require human review (9.2, 9.6).
- DOI policy: Every document version and each SC/rSC/AD/NP comment gets a DOI; ER does not (5.1, 5.5, 6.5, 10.3).
- Comment rules: Only verified users; question form; per-section references; explicit moderation states; rate limits (5.2–5.6).
- Versioning: Git-like history, diff views, per-section visibility, rollback capability (6.x).
- Identity: ORCID integration for authors; OAuth2 for APIs (8.1, 8.5, 11.1–11.3).
- Data model: PostgreSQL for metadata, JATS-XML for structured content, long-term archival (11.x).
- Transparency & logging: Comprehensive audit logs for actions and AI prompts/outputs (8.5, 9.2, 12.4).
- Trust-level classification and filters across UI and exports (9.4, 10.x).

---

## 3. Thematic Improvement Areas

### A. Governance & RBAC
- Rationale: Enforce the strict role capabilities matrix (2.3, 7.2) to protect editorial integrity and legal responsibilities.
- Proposed changes:
  1) Review and align Django Groups/Permissions to match the matrix (Leser, Kommentator, Autor, Moderator, Review Editor, Editorial Office, Admin). Ensure default groups exist (migration) and are assigned on registration/role change.
  2) Add permission checks at API layer for /documents, /comments, /review, /ai endpoints based on matrix.
  3) Admin/Editorial Office UI to manage role escalations; audit every change.
- Acceptance criteria:
  - Permission tests per role for all critical endpoints; unauthorized paths return 403.
  - Audit log entries for role changes with who/when/why.

### B. Document Model, Versioning & DOI
- Rationale: Version transparency and DOI assignment are core to citability and scholarly provenance (6.x; 10.3).
- Proposed changes:
  1) Persist JATS-XML per document version; ensure vX.Y scheme stored and enforced.
  2) Implement per-section anchors and optional per-section version view (store stable IDs per section in JATS).
  3) Add automatic DOI assignment on publish of a new primary version; configure provider (Crossref/DataCite) via settings.
  4) Create a timeline event log for document lifecycle (submission, review milestones, publish events) to drive UI.
  5) Provide rollback-to-version operation restricted to Editorial Office.
- Acceptance criteria:
  - New versions receive DOIs; timeline shows dated events; diff endpoint available; rollback audited.

### C. Comments & Moderation
- Rationale: Scientific discussion requires structured types, moderation, and citability (5.x).
- Proposed changes:
  1) Enforce comment types: SC, rSC, ER, AD, NP. Validate fields (question-form text, reference target, optional citations).
  2) Assign DOIs for SC/rSC/AD/NP upon acceptance; exclude ER from DOI.
  3) Moderation workflow states: new → accepted/rejected (with reason). Store moderator, timestamps.
  4) Rate limits: max 10 KI comments per document (1–2 per section); human comments: max 2 per section per user per day.
  5) Side-panel API: return comments grouped by section with anchors and status/color labels.
- Acceptance criteria:
  - Tests confirm validator behavior, DOI assignment rules, limits enforcement, and moderation transitions.

### D. Review Workflow
- Rationale: eLife-inspired process requires tracked assignments, statuses, and summary-to-author feedback (3.x; 7.1).
- Proposed changes:
  1) /review endpoints: start review, assign reviewers, track two reviews + editor comment, internal discussion, summary recommendation.
  2) Connect review outcomes to document status and next version creation triggers.
  3) Optional: expose rSC submission path for authors tied to SC threads.
- Acceptance criteria:
  - Review statuses visible via API; permissions enforced; author receives actionable summary.

### E. AI Assistant (Passive, Logged, Source-backed)
- Rationale: Improve discoverability of issues while maintaining human control and transparency (9.x).
- Proposed changes:
  1) /ai endpoint: generate question-form suggestions only; require RAG with approved sources; include source metadata + trust level.
  2) Enforce global caps: ≤10 AI comments per document; ≤2 per section; all marked as pending until moderator acceptance.
  3) Prompt/version logging: store prompt, model, temperature, context docs, time, requesting role.
  4) Configurations: allow model selection and prompt templates editable by Editorial Office/Admin; version these configs.
- Acceptance criteria:
  - AI outputs include sources and trust; logs persisted; rate limits and role checks active; no direct publish without acceptance.

### F. Trust Model & Provenance
- Rationale: Users must assess evidence quality quickly (9.4; 10.x).
- Proposed changes:
  1) Introduce TrustLevel field/enumeration for sources and comments; calculate or set via moderation.
  2) UI flags (🟢/🟡/🔴) and filters; export trust levels in metadata.
- Acceptance criteria:
  - Filtering works in API; exports include trust fields; UI labels rendered.

### G. APIs & Security
- Rationale: Safe, interoperable access (8.2; 8.5).
- Proposed changes:
  1) Align endpoints to spec: /documents, /comments, /users, /review, /ai with OpenAPI updates (swagger.json).
  2) OAuth2-based authentication for API clients; ensure RBAC per endpoint.
  3) Add per-user and per-IP rate limiting; CSRF/HTTPS enforcement.
  4) Comprehensive audit logging for CRUD and moderation decisions.
- Acceptance criteria:
  - OpenAPI matches behavior; security tests pass; audit logs present.

### H. Import/Export & Archival
- Rationale: Interoperability with repositories and long-term access (11.x).
- Proposed changes:
  1) JATS-XML import/export pipelines; map required fields (title, authors + ORCID, abstracts, sections, references).
  2) PDF/A generation including version and comment overlays.
  3) BibTeX/RIS export for literature and comment DOIs.
  4) Integrations: Crossref/DataCite, ORCID OAuth, optional PMC exports.
- Acceptance criteria:
  - Round-trip import/export tests; DOI and ORCID links verified; PDF/A validates.

### I. Frontend UX (Summary for Coordination)
- Rationale: Communicate status and provenance visually (5.3; 6.3; 10.2).
- Proposed changes (to coordinate with frontend):
  - Side comment panel with color labels and DOI links; line anchors.
  - Timeline view with version events; diff viewer (green/red changes).
  - Trust-level icons and filters; AI suggestion badges (hellgrün, „KI-Vorschlag“).
  - Role-sensitive actions and visibility.
- Acceptance criteria: Usability tests; accessibility checks; deep-linking to sections and comments.

### J. Observability, Logging & Compliance
- Rationale: Auditability and DSGVO compliance (8.5; 12.4).
- Proposed changes:
  1) Central structured logging (API calls, data changes, AI usage) with retention policy.
  2) GDPR features: data export/deletion for users where applicable; consent for logging AI interactions.
  3) Admin dashboards/reports: transparency reports for sources, prompts, model versions.
- Acceptance criteria: Logs complete and queryable; data subject requests supported; transparency reports exportable.

### K. Performance & Scalability
- Rationale: Ensure smooth UX as content grows.
- Proposed changes:
  1) Caching for heavy endpoints (document diffs, timelines, comment lists).
  2) Background jobs for DOI registration, PDF/A creation, RAG indexing.
  3) Database indexing for common filters (document, section, type, status, trust, created_at).
- Acceptance criteria: Latency and throughput SLOs met under test load.

---

## 4. Phased Roadmap & Milestones
- Phase 0 – Requirements consolidation (1–2 weeks)
  - Locate/author docs/requirements.md; reconcile with guidelines; finalize acceptance criteria.
- Phase 1 – RBAC & Comments Compliance (2–3 weeks)
  - Permission matrix enforcement; comment validators; moderation + DOI rules; basic timeline events.
- Phase 2 – Versioning & DOI for Documents (2–3 weeks)
  - JATS per version; diff API; publish/rollback; DOI provider integration.
- Phase 3 – AI Assist (2–3 weeks)
  - /ai endpoint with RAG, trust annotations, logging, rate caps; moderation queue integration.
- Phase 4 – Import/Export & Archival (2–3 weeks)
  - JATS import/export; PDF/A; BibTeX/RIS; external repository integration.
- Phase 5 – Security/Compliance/Observability (ongoing)
  - OAuth2, rate limiting, audit dashboards, GDPR tooling.

Dependencies: Phase 1 before 2; 2 before 3; 3 can run parallel with 4 in parts; 5 continuous.

---

## 5. Risks & Open Questions
- Missing docs/requirements.md: This plan relies on guidelines only. Action: add/obtain docs/requirements.md and re-sync.
- DOI provider choice (Crossref vs DataCite) and account credentials; sandbox availability.
- OAuth2 provider selection and compatibility with existing auth.
- Storage and cost for long-term logs and PDF/A artifacts.
- RAG corpus curation policy; approved sources and update cadence.
- Moderation SLAs and escalation paths; legal review for comment policies.

---

## 6. Acceptance Criteria Summary (by Area)
- RBAC: Unit/integration tests enforce matrix; audit logs for role changes.
- Versioning/DOI: Each publish creates a DOI; diff and rollback work; timeline populated.
- Comments: Type/format validators; moderation/state transitions; rates enforced; DOI rules followed.
- Review: Start/assign/status endpoints; editor summary to authors.
- AI: Only questions; sources + trust included; logs complete; rate caps; human acceptance required.
- Trust: API filters and UI icons; exports include trust.
- Security: OAuth2, rate limiting; OpenAPI up-to-date; 403/401 paths verified.
- Import/Export: JATS, PDF/A, BibTeX/RIS validated; external integrations tested.
- Observability/GDPR: Logs complete; DSR flows available; transparency reports accessible.

---

## 7. Mapping to Current Repository (initial)
- Backend modules observed: core, comments, publications, ai_assistant, tests, swagger.json.
- Likely mappings:
  - comments app → Comment types, moderation, limits, DOIs for SC/rSC/AD/NP; validators + serializers.
  - publications app → DocumentVersion model, JATS storage, DOI assignment, timeline events, diff API.
  - ai_assistant app → /ai endpoint, RAG, prompt logging, trust annotations.
  - core app → Users, roles/groups, ORCID, email, analytics, DOI service adapters.
- Immediate next tasks: finalize docs/requirements.md; align tests and OpenAPI; plan migrations for trust levels and logs.

---

## 8. Implementation Notes
- Prefer additive migrations; avoid breaking schema changes.
- Feature-flag AI functions until policy sign-off.
- Introduce service interfaces for DOI and RAG to allow provider swapping.
- Keep Windows/PowerShell scripts updated for ops tasks where applicable.
