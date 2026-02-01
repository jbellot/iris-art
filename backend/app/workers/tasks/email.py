"""Email tasks for Celery background processing."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.email.send_verification_email")
def send_verification_email(email: str, token: str) -> None:
    """Send email verification link to user.

    Args:
        email: User email address
        token: Verification token

    Note:
        Currently logs the verification link instead of sending actual email.
        Email service provider (ESP) selection is pending.
    """
    verification_link = f"http://localhost:8000/api/v1/auth/verify-email?token={token}"

    # LOG instead of sending (ESP to be determined)
    print(f"\n{'='*80}")
    print(f"VERIFICATION EMAIL to {email}")
    print(f"Link: {verification_link}")
    print(f"{'='*80}\n")


@celery_app.task(name="app.workers.tasks.email.send_password_reset_email")
def send_password_reset_email(email: str, token: str) -> None:
    """Send password reset link to user.

    Args:
        email: User email address
        token: Password reset token

    Note:
        Currently logs the reset link instead of sending actual email.
        Email service provider (ESP) selection is pending.
    """
    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={token}"

    # LOG instead of sending (ESP to be determined)
    print(f"\n{'='*80}")
    print(f"PASSWORD RESET EMAIL to {email}")
    print(f"Link: {reset_link}")
    print(f"{'='*80}\n")
