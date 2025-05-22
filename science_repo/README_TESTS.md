# Living Science Documents - Test Documentation

## Overview

This document provides an overview of the test coverage for the Living Science Documents project and recommendations for fixing test issues.

## Test Coverage

The project includes comprehensive unit tests for all major components:

### Core App
- User model tests
- User serializer tests
- Authentication API tests (login, ORCID)
- User management API tests

### Publications App
- Publication model tests
- DocumentVersion model tests
- Publication API tests
- DocumentVersion API tests

### Comments App
- CommentType model tests
- Comment model tests
- CommentAuthor model tests
- CommentReference model tests
- Comment API tests

### AI Assistant App
- AIModel model tests
- AIPrompt model tests
- AICommentSuggestion model tests
- AIReference model tests
- AIFeedback model tests
- AI Assistant API tests

## Test Issues

When running the tests, several issues were encountered:

1. **Model Field Clashes**: Fixed by adding appropriate `related_name` arguments to ForeignKey fields:
   - Updated `core.Comment.status_user` to use `related_name="core_moderated_comments"`
   - Updated `core.Author.user` to use `related_name="core_authors"`
   - Updated `publications.Author.user` to use `related_name="publication_authors"`

2. **Database Setup Issues**: Many tests fail due to database setup issues, including:
   - Missing tables or fields
   - Incorrect test data or assumptions
   - Foreign key constraints

3. **API Test Issues**: Some API tests fail due to:
   - Incorrect URL patterns
   - Permission issues
   - Missing or incorrect test data

## Recommendations

To fix the test issues, the following steps are recommended:

1. **Database Migrations**:
   - Run `python manage.py makemigrations` to create migration files for the model changes
   - Run `python manage.py migrate` to apply the migrations to the database

2. **Test Data Setup**:
   - Review the test setup code to ensure all required objects are created
   - Use `setUp` and `setUpTestData` methods consistently
   - Ensure test data matches model constraints

3. **API Test Fixes**:
   - Verify URL patterns in the tests match the actual URL configuration
   - Check permission classes and authentication requirements
   - Update test assertions to match expected behavior

4. **Mock External Services**:
   - Use mocking for external services (ORCID, DOI, etc.) to avoid test failures
   - Consider using `unittest.mock` or `pytest-mock` for this purpose

5. **Test Isolation**:
   - Ensure tests are isolated and don't depend on each other
   - Use `TransactionTestCase` for tests that need transaction rollback

## Next Steps

1. Fix the database migration issues
2. Address the most critical test failures first (core app tests)
3. Fix the API test issues
4. Implement mocking for external services
5. Run tests with coverage reporting to identify untested code