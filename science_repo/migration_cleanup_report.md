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