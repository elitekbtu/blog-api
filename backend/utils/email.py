# Python modules
import logging

# Django modules
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import override as translation_override

logger = logging.getLogger(__name__)


def send_welcome_email(user) -> None:
    """
    Send a welcome email to a newly registered user.

    The email is rendered from templates and delivered in the user's own
    ``preferred_language``, regardless of the language that is active on
    the current request/thread at call time.

    Templates used:
        emails/welcome_subject.txt   – single-line plain-text subject
        emails/welcome_body.txt      – plain-text fallback body
        emails/welcome_body.html     – HTML body

    For local development the email is printed to the console
    (EMAIL_BACKEND = console).  In production it is sent via SMTP.
    """

    lang = getattr(user, "preferred_language", None) or "en"
    context = {"user": user}

    try:
        with translation_override(lang):
            subject = render_to_string(
                "emails/welcome_subject.txt", context
            ).strip()
            body_txt = render_to_string("emails/welcome_body.txt", context)
            body_html = render_to_string("emails/welcome_body.html", context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=body_txt,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        message.attach_alternative(body_html, "text/html")
        message.send()

        logger.info(
            f"Welcome email sent: user_id={user.id}, email={user.email}, lang={lang}"
        )

    except Exception:
        logger.exception(
            f"Failed to send welcome email: user_id={user.id}, email={user.email}"
        )
