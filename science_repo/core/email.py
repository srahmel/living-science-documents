from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """
    Service for sending emails to users.
    
    This service provides methods for sending various types of emails:
    - Notification emails for new comments
    - Notification emails for comment status changes
    - Notification emails for publication status changes
    - Welcome emails for new users
    - Password reset emails
    """
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None, from_email=None):
        """
        Send an email.
        
        Args:
            subject (str): The email subject
            message (str): The email message (plain text)
            recipient_list (list): List of recipient email addresses
            html_message (str, optional): HTML version of the message
            from_email (str, optional): Sender email address
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        if html_message:
            # Send HTML email with plain text alternative
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            return email.send() > 0
        else:
            # Send plain text email
            return send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            ) > 0
    
    @staticmethod
    def send_comment_notification(comment, recipient_list):
        """
        Send a notification email about a new comment.
        
        Args:
            comment: The comment object
            recipient_list (list): List of recipient email addresses
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        subject = f"New comment on {comment.document_version}"
        
        # Prepare context for the template
        context = {
            'comment': comment,
            'document_version': comment.document_version,
            'publication': comment.document_version.publication,
            'comment_url': f"{settings.FRONTEND_URL}/publications/{comment.document_version.publication.id}/versions/{comment.document_version.id}/comments/{comment.id}",
        }
        
        # Render HTML message from template
        html_message = render_to_string('emails/comment_notification.html', context)
        
        # Create plain text version by stripping HTML
        plain_message = strip_tags(html_message)
        
        return EmailService.send_email(
            subject=subject,
            message=plain_message,
            recipient_list=recipient_list,
            html_message=html_message
        )
    
    @staticmethod
    def send_comment_status_notification(comment, recipient_list):
        """
        Send a notification email about a comment status change.
        
        Args:
            comment: The comment object
            recipient_list (list): List of recipient email addresses
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        subject = f"Comment status update: {comment.get_status_display()}"
        
        # Prepare context for the template
        context = {
            'comment': comment,
            'document_version': comment.document_version,
            'publication': comment.document_version.publication,
            'comment_url': f"{settings.FRONTEND_URL}/publications/{comment.document_version.publication.id}/versions/{comment.document_version.id}/comments/{comment.id}",
        }
        
        # Render HTML message from template
        html_message = render_to_string('emails/comment_status_notification.html', context)
        
        # Create plain text version by stripping HTML
        plain_message = strip_tags(html_message)
        
        return EmailService.send_email(
            subject=subject,
            message=plain_message,
            recipient_list=recipient_list,
            html_message=html_message
        )
    
    @staticmethod
    def send_publication_status_notification(document_version, recipient_list):
        """
        Send a notification email about a publication status change.
        
        Args:
            document_version: The document version object
            recipient_list (list): List of recipient email addresses
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        subject = f"Publication status update: {document_version.get_status_display()}"
        
        # Prepare context for the template
        context = {
            'document_version': document_version,
            'publication': document_version.publication,
            'publication_url': f"{settings.FRONTEND_URL}/publications/{document_version.publication.id}/versions/{document_version.id}",
        }
        
        # Render HTML message from template
        html_message = render_to_string('emails/publication_status_notification.html', context)
        
        # Create plain text version by stripping HTML
        plain_message = strip_tags(html_message)
        
        return EmailService.send_email(
            subject=subject,
            message=plain_message,
            recipient_list=recipient_list,
            html_message=html_message
        )
    
    @staticmethod
    def send_welcome_email(user):
        """
        Send a welcome email to a new user.
        
        Args:
            user: The user object
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        subject = "Welcome to Living Science Documents"
        
        # Prepare context for the template
        context = {
            'user': user,
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        
        # Render HTML message from template
        html_message = render_to_string('emails/welcome.html', context)
        
        # Create plain text version by stripping HTML
        plain_message = strip_tags(html_message)
        
        return EmailService.send_email(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )
        
    @staticmethod
    def send_password_reset_email(user, token):
        """
        Send a password reset email to a user.
        
        Args:
            user: The user object
            token: The password reset token
            
        Returns:
            bool: True if the email was sent successfully, False otherwise
        """
        subject = "Reset Your Password - Living Science Documents"
        
        # Create the reset URL with the token
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={user.email}"
        
        # Prepare context for the template
        context = {
            'user': user,
            'reset_url': reset_url,
        }
        
        # Render HTML message from template
        html_message = render_to_string('emails/password_reset.html', context)
        
        # Create plain text version by stripping HTML
        plain_message = strip_tags(html_message)
        
        return EmailService.send_email(
            subject=subject,
            message=plain_message,
            recipient_list=[user.email],
            html_message=html_message
        )