from typing import Any
from django.db.models import Model, DateTimeField
from django.utils import timezone as django_timezone


class AbstractTimeStamptModel(Model):
    """
    AbstractTimeStamptModel is an abstract model,
    that provides timestamp fields for created,
    updated, and deleted times.

    Fields:
        - created_at: DateTimeField
        - updated_at: DateTimeField
        - deleted_at: DateTimeField
    """

    created_at = DateTimeField(
        auto_now_add=True,
    )
    updated_at = DateTimeField(
        auto_now=True,
    )
    deleted_at = DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        abstract = True

        def delete(self, *args: tuple[Any, ...], **kwargs: dict[Any, Any]) -> None:
            """
            Soft delete the object
            by setting the deleted_at
            field to the current time.

                Args:
                    *args: tuple of positional arguments
                    **kwargs: dict of keyword arguments
                Returns:
                    None
            """

            self.deleted_at = django_timezone.now()
            self.save(update_fields=["deleted_at"])
