# Living Science Documents - Backend API

Last updated: 2025-09-02 00:57 (local)

This repository contains the backend API for the Living Science Documents platform, a collaborative, versionable, scientifically supervised publication and discussion platform.

## Project Structure

The project is organized into several Django apps:

- **core**: User management, authentication, and ORCID integration
- **publications**: Publication, document version, and review management
- **comments**: Comment system with moderation and different comment types
- **ai_assistant**: AI integration for generating and managing comment suggestions

## API Endpoints

The API is organized into the following namespaces:

- `/api/auth/`: Authentication endpoints
- `/api/publications/`: Publication management endpoints
- `/api/comments/`: Comment system endpoints
- `/api/ai/`: AI integration endpoints

## API Documentation (Swagger)

Note: The live schema at /swagger.json is generated from the current URL configuration and serializers using drf-yasg. If you find a mismatch between code and docs, clear caches and refresh; no manual editing of swagger.json in the repo is required.

The API is documented using Swagger/OpenAPI. You can access the documentation at:

- `/swagger/`: Interactive Swagger UI for exploring and testing the API (generated dynamically by drf-yasg)
- `/redoc/`: ReDoc UI for a more readable documentation experience
- `/swagger.json` or `/swagger.yaml`: Raw schema files (live, generated from code; prefer these over any static file in the repo)

### How to use Swagger UI:

To export the current OpenAPI schema to a file:
- PowerShell: `Invoke-WebRequest http://localhost:8000/swagger.json -OutFile swagger.json`
- curl: `curl -s http://localhost:8000/swagger.json > swagger.json`

1. Start the development server: `python manage.py runserver`
2. Navigate to `http://localhost:8000/swagger/` in your browser
3. You'll see all available endpoints organized by namespace
4. Click on any endpoint to expand it and see details (parameters, request body, responses)
5. You can try out endpoints directly from the UI by clicking the "Try it out" button
6. For authenticated endpoints, you'll need to click the "Authorize" button and provide your JWT token

### Authentication

- `POST /api/auth/register/`: Register a new user
- `POST /api/auth/login/`: Login with username and password
- `GET /api/auth/csrf/`: Get a CSRF token for use in frontend applications
- `GET /api/auth/orcid/login/`: Redirect to ORCID for authentication
- `GET /api/auth/orcid/callback/`: Handle ORCID callback
- `POST /api/auth/refresh/`: Refresh JWT token

### Publications

- `GET /api/publications/publications/`: List all publications
- `POST /api/publications/publications/`: Create a new publication
- `GET /api/publications/publications/{id}/`: Get publication details
- `PUT /api/publications/publications/{id}/`: Update a publication
- `DELETE /api/publications/publications/{id}/`: Delete a publication
- `GET /api/publications/publications/{id}/versions/`: Get all versions of a publication
- `GET /api/publications/publications/{id}/current_version/`: Get the current version of a publication

- `GET /api/publications/document-versions/`: List all document versions
- `POST /api/publications/document-versions/`: Create a new document version
- `GET /api/publications/document-versions/{id}/`: Get document version details
- `PUT /api/publications/document-versions/{id}/`: Update a document version
- `DELETE /api/publications/document-versions/{id}/`: Delete a document version
- `POST /api/publications/document-versions/{id}/submit_for_review/`: Submit a document version for review
- `POST /api/publications/document-versions/{id}/generate_keywords/`: Generate AI keywords for a document version
- `POST /api/publications/document-versions/{id}/publish/`: Publish a document version
- `GET /api/publications/document-versions/{id}/pdf/`: Download a PDF version of a document
- `GET /api/publications/document-versions/{id}/jats/`: Export a document version to JATS-XML format
- `GET /api/publications/document-versions/{id}/repository/`: Export a document version to a repository (PubMed Central, Europe PMC, institutional repositories)

- `GET /api/publications/review-processes/`: List all review processes
- `POST /api/publications/review-processes/`: Create a new review process
- `GET /api/publications/review-processes/{id}/`: Get review process details
- `PUT /api/publications/review-processes/{id}/`: Update a review process
- `DELETE /api/publications/review-processes/{id}/`: Delete a review process
- `POST /api/publications/review-processes/{id}/complete_review/`: Complete a review process

- `GET /api/publications/reviewers/`: List all reviewers
- `POST /api/publications/reviewers/`: Create a new reviewer
- `GET /api/publications/reviewers/{id}/`: Get reviewer details
- `PUT /api/publications/reviewers/{id}/`: Update a reviewer
- `DELETE /api/publications/reviewers/{id}/`: Delete a reviewer
- `POST /api/publications/reviewers/{id}/accept_invitation/`: Accept a review invitation
- `POST /api/publications/reviewers/{id}/decline_invitation/`: Decline a review invitation
- `POST /api/publications/reviewers/{id}/complete_review/`: Complete a review

### Comments

- `GET /api/comments/comment-types/`: List all comment types
- `POST /api/comments/comment-types/`: Create a new comment type
- `GET /api/comments/comment-types/{id}/`: Get comment type details
- `PUT /api/comments/comment-types/{id}/`: Update a comment type
- `DELETE /api/comments/comment-types/{id}/`: Delete a comment type

- `GET /api/comments/comments/`: List all comments
- `POST /api/comments/comments/`: Create a new comment
- `GET /api/comments/comments/{id}/`: Get comment details
- `PUT /api/comments/comments/{id}/`: Update a comment
- `DELETE /api/comments/comments/{id}/`: Delete a comment
- `POST /api/comments/comments/{id}/submit/`: Submit a comment for moderation
- `POST /api/comments/comments/{id}/create_chat/`: Create a chat for a comment

- `GET /api/comments/comment-chats/`: List all comment chats
- `POST /api/comments/comment-chats/`: Create a new comment chat
- `GET /api/comments/comment-chats/{id}/`: Get comment chat details
- `PUT /api/comments/comment-chats/{id}/`: Update a comment chat
- `DELETE /api/comments/comment-chats/{id}/`: Delete a comment chat
- `POST /api/comments/comment-chats/{id}/add_message/`: Add a message to a comment chat

- `GET /api/comments/chat-messages/`: List all chat messages
- `POST /api/comments/chat-messages/`: Create a new chat message
- `GET /api/comments/chat-messages/{id}/`: Get chat message details
- `PUT /api/comments/chat-messages/{id}/`: Update a chat message
- `DELETE /api/comments/chat-messages/{id}/`: Delete a chat message

- `GET /api/comments/comment-moderations/`: List all comment moderations
- `POST /api/comments/comment-moderations/`: Create a new comment moderation
- `GET /api/comments/comment-moderations/{id}/`: Get comment moderation details
- `PUT /api/comments/comment-moderations/{id}/`: Update a comment moderation
- `DELETE /api/comments/comment-moderations/{id}/`: Delete a comment moderation
- `GET /api/comments/comment-moderations/pending_comments/`: Get comments pending moderation
- `POST /api/comments/comment-moderations/moderate_comment/`: Moderate a comment

### AI Integration

- `GET /api/ai/ai-models/`: List all AI models
- `POST /api/ai/ai-models/`: Create a new AI model
- `GET /api/ai/ai-models/{id}/`: Get AI model details
- `PUT /api/ai/ai-models/{id}/`: Update an AI model
- `DELETE /api/ai/ai-models/{id}/`: Delete an AI model

- `GET /api/ai/ai-prompts/`: List all AI prompts
- `POST /api/ai/ai-prompts/`: Create a new AI prompt
- `GET /api/ai/ai-prompts/{id}/`: Get AI prompt details
- `PUT /api/ai/ai-prompts/{id}/`: Update an AI prompt
- `DELETE /api/ai/ai-prompts/{id}/`: Delete an AI prompt

- `GET /api/ai/ai-comment-suggestions/`: List all AI comment suggestions
- `POST /api/ai/ai-comment-suggestions/`: Create a new AI comment suggestion
- `GET /api/ai/ai-comment-suggestions/{id}/`: Get AI comment suggestion details
- `PUT /api/ai/ai-comment-suggestions/{id}/`: Update an AI comment suggestion
- `DELETE /api/ai/ai-comment-suggestions/{id}/`: Delete an AI comment suggestion
- `POST /api/ai/ai-comment-suggestions/{id}/approve/`: Approve an AI comment suggestion
- `POST /api/ai/ai-comment-suggestions/{id}/reject/`: Reject an AI comment suggestion
- `POST /api/ai/ai-comment-suggestions/{id}/modify_and_approve/`: Modify and approve an AI comment suggestion
- `POST /api/ai/ai-comment-suggestions/generate/`: Generate AI comment suggestions for a document version

## Setup and Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: 
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with the following variables:
   ```
   DJANGO_SECRET_KEY=your_secret_key
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

   POSTGRES_DB=living_science
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432

   ORCID_CLIENT_ID=your_orcid_client_id
   ORCID_CLIENT_SECRET=your_orcid_client_secret
   FRONTEND_URL=http://localhost:3000

   # Used for correct schema/servers in Swagger generation
   API_BASE_URL=http://localhost:8000
   API_PATH=/

   CORS_ALLOW_ALL_ORIGINS=True
   CORS_ALLOWED_ORIGINS=http://localhost:3000
   ```
6. Run migrations: `python manage.py migrate`
7. Create a superuser: `python manage.py createsuperuser`
8. Run the server: `python manage.py runserver`

## Workflow

The Living Science Documents platform implements the following workflows:

### Publication Workflow

1. Author creates a new publication and document version
2. Author submits the document version for review
3. Editorial board assigns reviewers
4. Reviewers review the document and provide feedback
5. Editorial board completes the review process
6. If accepted, the document version is published
7. If revision is required, the author creates a new document version
8. The process repeats until the document is published or rejected

### Comment Workflow

1. User creates a comment on a document version
2. User submits the comment for moderation
3. Moderator reviews the comment
4. If approved, the comment is published
5. If rejected, the comment is marked as rejected
6. If revision is required, the comment is returned to draft status

### Chat Workflow

1. User creates a chat for a comment or uses an existing chat
2. User adds messages to the chat
3. Other users can view the chat and add their own messages
4. All logged-in users can participate in the chat
5. Each comment has its own separate chat thread

### AI Integration Workflow

1. User requests AI-generated comment suggestions for a document version
2. AI generates comment suggestions
3. User reviews the suggestions
4. User can approve, reject, or modify and approve each suggestion
5. Approved suggestions are converted to comments
6. Comments follow the standard comment workflow

## Permissions and Roles

The system implements role-based access control:

- **Anonymous users**: Can view published content
- **Authenticated users**: Can create comments and provide feedback
- **Authors**: Can create and edit their own publications and document versions
- **Reviewers**: Can review assigned document versions
- **Moderators**: Can moderate comments
- **Editorial board**: Can manage publications, document versions, and review processes
- **Admins**: Can manage all aspects of the system, including AI models and prompts

## Technologies Used

- Django 5.2
- Django REST Framework
- PostgreSQL
- JWT Authentication
- ORCID Integration
- CORS Support
