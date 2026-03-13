import zoneinfo

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class TimezoneValidator:

    def __call__(self, value):

        try:
            zoneinfo.ZoneInfo(value)
        except Exception:
            raise serializers.ValidationError(
                _("Invalid timezone. Must be a valid IANA timezone identifier.")
            )