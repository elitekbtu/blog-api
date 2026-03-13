from django.utils import timezone
from django.utils.formats import date_format
from zoneinfo import ZoneInfo


def format_user_datetime(dt, user):
    """
    Convert datetime to user's timezone and format according to locale.
    """

    if not dt:
        return None

    if user and user.is_authenticated and getattr(user, "timezone", None):
        tz = ZoneInfo(user.timezone)
    else:
        tz = ZoneInfo("UTC")

    dt = timezone.localtime(dt, tz)

    return date_format(dt, format="DATETIME_FORMAT", use_l10n=True)