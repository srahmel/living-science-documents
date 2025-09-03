# Migration Cleanup Report

## Issue
The project had duplicate model definitions across different apps, causing migration failures when tables or data already existed.

## Analysis
After examining all migration files, I found the following duplications:

1. **Core app vs. Comments app**:
   - CommentType model
   - Comment model
   - CommentAuthor model
   - ConflictOfInterest model

2. **Core app vs. Publications app**:
   - Publication model
   - Author model
   - Keyword model
   - Document/DocumentVersion models

## Solution
I kept the newer, more complete versions of these models in their specialized apps (comments and publications) and removed the duplicates from the core app.

## Modified Files

1. `core/migrations/0001_initial.py`
   - Removed duplicate models: CommentType, Comment, CommentAuthor, ConflictOfInterest, Publication, Author, Keyword, Document
   - Kept only: User, SavedSearch, SearchAttribute, UserAlias

2. `core/migrations/0002_alter_author_user_alter_comment_status_user.py`
   - Removed operations that altered Author and Comment models (which no longer exist in core app)
   - Kept the migration file with empty operations to maintain migration history

3. `core/migrations/0004_alter_publication_meta_doi.py`
   - Removed operation that altered Publication model (which no longer exist in core app)
   - Kept the migration file with empty operations to maintain migration history

## Conclusion
The migration files have been cleaned up to remove duplications while maintaining the migration history. The specialized apps (comments and publications) now contain the definitive versions of their respective models.

This should resolve the migration failures caused by duplicate table creations and data insertions.
# Publications Migration Squash (Option B)

Date: 2025-09-03

Summary:
- We squashed the publications app migrations to fix inconsistent migration dependencies.
- All migration files under publications/migrations were removed except __init__.py.
- A temporary placeholder 0001_initial.py was created (no operations) to satisfy cross-app dependencies during makemigrations.
- Ran: python manage.py makemigrations publications → created publications/0002_initial.py containing the full schema derived from publications/models.py.
- Updated cross-app migration dependencies:
  - comments/0001_initial.py now depends on ("publications", "0002_initial").
  - ai_assistant/0001_initial.py now depends on ("publications", "0002_initial").
- Dropped all database tables using management command: python manage.py drop_all_tables
- Applied all migrations cleanly: python manage.py migrate --noinput.

Resulting migration state (python manage.py showmigrations publications):
- [X] 0001_initial (placeholder)
- [X] 0002_initial (actual schema)

Rationale:
- The previous migration chain had missing/renamed dependencies (NodeNotFoundError). Squashing avoids chasing historical inconsistencies.
- Keeping a placeholder 0001 allows dependent apps to continue referencing publications.0001 without renumbering their entire history; they now explicitly point to 0002 to ensure the schema exists when needed.

Implications for collaborators:
- If you have a local DB, run: python manage.py drop_all_tables && python manage.py migrate
- Ensure your working copy includes the updated dependencies in comments and ai_assistant migrations.
- Do not reintroduce old publications migrations; the new baseline is 0001 (placeholder) + 0002 (schema).

Next steps (optional):
- In a follow-up PR, we can squash 0001 (placeholder) and 0002 (schema) into a single 0001_initial and adjust dependencies back to 0001. This requires coordination because it changes migration hashes and requires a DB reset.
