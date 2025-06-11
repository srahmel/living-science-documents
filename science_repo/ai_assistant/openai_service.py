"""
OpenAI service for the AI assistant app.
This service handles the communication with the OpenAI API.
"""

import openai
import time
from django.conf import settings
from .models import AIModel, AIPrompt, AICommentSuggestion, AIPromptLog, AIReference
from publications.models import Keyword

class OpenAIService:
    """
    Service for interacting with the OpenAI API.
    """

    @staticmethod
    def initialize_client():
        """
        Initialize the OpenAI client with the API key and organization.
        """
        openai.api_key = settings.OPENAI_API_KEY
        if settings.OPENAI_ORGANIZATION:
            openai.organization = settings.OPENAI_ORGANIZATION
        openai.api_base = settings.OPENAI_API_BASE

    @staticmethod
    def generate_comment_suggestions(document_version, ai_model, ai_prompt, user):
        """
        Generate AI comment suggestions for a document version.

        Args:
            document_version: The document version to generate suggestions for
            ai_model: The AI model to use
            ai_prompt: The AI prompt to use
            user: The user who initiated the generation

        Returns:
            A list of AICommentSuggestion objects
        """
        # Initialize the OpenAI client
        OpenAIService.initialize_client()

        # Start timing for execution time measurement
        start_time = time.time()

        # Prepare the document content
        document_content = f"""
        Title: {document_version.publication.title}
        Version: {document_version.version_number}

        Technical Abstract:
        {document_version.technical_abstract}

        Introduction:
        {document_version.introduction}

        Methodology:
        {document_version.methodology}

        Main Text:
        {document_version.main_text}

        Conclusion:
        {document_version.conclusion}
        """

        # Prepare the prompt
        prompt_text = ai_prompt.prompt_template.replace("{{text}}", document_content)

        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a scientific assistant that helps identify potential questions, issues, or areas for improvement in scientific documents. Your suggestions should be in the form of questions and should be specific, constructive, and relevant to the document content."},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            # Process the response
            suggestions = []

            # Extract the suggestions from the response
            suggestion_text = response.choices[0].message.content

            # Parse the suggestions (assuming they're numbered or separated by lines)
            suggestion_lines = [line.strip() for line in suggestion_text.split('\n') if line.strip()]

            # Create suggestion objects
            for i, line in enumerate(suggestion_lines):
                if '?' in line:  # Ensure it's a question
                    # Determine the section reference and line numbers (simplified)
                    section_reference = "Introduction" if "introduction" in line.lower() else \
                                       "Methodology" if "methodology" in line.lower() or "method" in line.lower() else \
                                       "Results" if "result" in line.lower() else \
                                       "Discussion" if "discussion" in line.lower() else \
                                       "Conclusion" if "conclusion" in line.lower() else \
                                       "General"

                    # Create the suggestion
                    suggestion = AICommentSuggestion.objects.create(
                        document_version=document_version,
                        ai_model=ai_model,
                        ai_prompt=ai_prompt,
                        content=line,
                        section_reference=section_reference,
                        status='pending',
                        confidence_score=response.choices[0].finish_reason == "stop" and 0.9 or 0.7  # Higher confidence if completed normally
                    )
                    suggestions.append(suggestion)

                    # Create a reference if applicable
                    if "reference" in line.lower() or "citation" in line.lower() or "literature" in line.lower():
                        AIReference.objects.create(
                            suggestion=suggestion,
                            title="Suggested Reference",
                            authors="Various Authors",
                            citation_text="The AI suggests checking relevant literature on this topic.",
                            trust_level="medium"
                        )

            # End timing
            execution_time = time.time() - start_time

            # Log the prompt execution
            AIPromptLog.objects.create(
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                user=user,
                input_context=f"Document: {document_version.publication.title} v{document_version.version_number}",
                output_text=suggestion_text,
                execution_time=execution_time,
                token_count=len(prompt_text.split()) + len(suggestion_text.split())  # Approximate token count
            )

            return suggestions

        except Exception as e:
            # Log the error
            AIPromptLog.objects.create(
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                user=user,
                input_context=f"Document: {document_version.publication.title} v{document_version.version_number}",
                output_text=f"Error: {str(e)}",
                execution_time=time.time() - start_time,
                token_count=len(prompt_text.split())  # Approximate token count
            )

            # Re-raise the exception
            raise e

    @staticmethod
    def generate_keywords(document_version, ai_model, user, max_keywords=5):
        """
        Generate AI keyword suggestions for a document version.

        Args:
            document_version: The document version to generate keywords for
            ai_model: The AI model to use
            user: The user who initiated the generation
            max_keywords: Maximum number of keywords to generate (default: 5)

        Returns:
            A list of Keyword objects created for the document version
        """
        # Initialize the OpenAI client
        OpenAIService.initialize_client()

        # Start timing for execution time measurement
        start_time = time.time()

        # Prepare the document content
        document_content = f"""
        Title: {document_version.publication.title}

        Technical Abstract:
        {document_version.technical_abstract}

        Introduction:
        {document_version.introduction}
        """

        # Prepare the prompt
        prompt_text = f"Based on the following scientific document, suggest {max_keywords} relevant keywords or key phrases that best represent the content. Return only the keywords, one per line, without numbering or additional text.\n\n{document_content}"

        try:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a scientific assistant that helps identify relevant keywords for scientific publications. Provide concise, specific keywords that accurately represent the document's content and would be useful for indexing and searching."},
                    {"role": "user", "content": prompt_text}
                ],
                max_tokens=100,  # Shorter response for keywords
                temperature=0.3,  # Lower temperature for more focused results
            )

            # Process the response
            keywords = []

            # Extract the keywords from the response
            keyword_text = response.choices[0].message.content

            # Parse the keywords (one per line)
            keyword_lines = [line.strip() for line in keyword_text.split('\n') if line.strip()]

            # Create keyword objects
            for keyword in keyword_lines[:max_keywords]:  # Limit to max_keywords
                # Create the keyword object
                keyword_obj = Keyword.objects.create(
                    document_version=document_version,
                    keyword=keyword
                )
                keywords.append(keyword_obj)

            # End timing
            execution_time = time.time() - start_time

            # Log the prompt execution
            AIPromptLog.objects.create(
                ai_model=ai_model,
                ai_prompt=None,  # No specific prompt object for keywords
                user=user,
                input_context=f"Document: {document_version.publication.title} v{document_version.version_number} - Keyword Generation",
                output_text=keyword_text,
                execution_time=execution_time,
                token_count=len(prompt_text.split()) + len(keyword_text.split())  # Approximate token count
            )

            return keywords

        except Exception as e:
            # Log the error
            AIPromptLog.objects.create(
                ai_model=ai_model,
                ai_prompt=None,  # No specific prompt object for keywords
                user=user,
                input_context=f"Document: {document_version.publication.title} v{document_version.version_number} - Keyword Generation",
                output_text=f"Error: {str(e)}",
                execution_time=time.time() - start_time,
                token_count=len(prompt_text.split())  # Approximate token count
            )

            # Re-raise the exception
            raise e
