import logging

from celery import shared_task

from apps.users.models import CustomUser
from utils.email import send_welcome_email

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_welcome_email_task(user_id: int) -> None:
    # Automatic retries matter for email tasks because SMTP providers and network
    # calls can fail transiently; retrying prevents dropping a welcome email due to
    # short outages or brief rate-limit windows.
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        logger.warning("Cannot send welcome email: user_id=%s not found", user_id)
        return

    send_welcome_email(user)
