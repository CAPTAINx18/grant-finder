import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(email_to: str, subject: str, html_content: str) -> bool:
    """Send an email using configured SMTP settings."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to

    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    try:
        # Establish connection to Mailpit/SMTP host
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, message.as_string())
        logger.info(f"Email successfully sent to {email_to} with subject: '{subject}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email_to} via SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT}: {e}")
        return False


def send_verification_email(email_to: str, token: str) -> bool:
    """Send verification email containing activation token."""
    subject = f"Verify your {settings.PROJECT_NAME} Account"
    link = f"http://localhost:3000/verify-email?token={token}"
    html_content = f"""
    <html>
        <body style="font-family: sans-serif; color: #333; line-height: 1.6; padding: 20px;">
            <h2 style="color: #4f46e5;">Welcome to {settings.PROJECT_NAME}!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p style="font-size: 12px; color: #666;">This link expires in 24 hours. If you did not sign up, please ignore this email.</p>
        </body>
    </html>
    """
    return send_email(email_to, subject, html_content)


def send_reset_password_email(email_to: str, token: str) -> bool:
    """Send password reset email containing recovery token."""
    subject = f"Reset your {settings.PROJECT_NAME} Password"
    link = f"http://localhost:3000/reset-password?token={token}"
    html_content = f"""
    <html>
        <body style="font-family: sans-serif; color: #333; line-height: 1.6; padding: 20px;">
            <h2 style="color: #4f46e5;">Password Reset Request</h2>
            <p>You requested a password reset for your {settings.PROJECT_NAME} account. Click the button below to recovery your account and choose a new password:</p>
            <p style="margin: 24px 0;">
                <a href="{link}" style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p style="font-size: 12px; color: #666;">This recovery link expires in 2 hours. If you did not request this change, you can safely ignore this email.</p>
        </body>
    </html>
    """
    return send_email(email_to, subject, html_content)
