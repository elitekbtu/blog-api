from typing import Any

from django.db.models import (
    CharField,
    EmailField,
    BooleanField,
    DateTimeField,
    ImageField,
)
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from backend.apps.abstract.models import AbstractTimeStamptModel


class CustomUserManager(BaseUserManager):
    """
    Custom UserManager for User Model
    """

    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> "CustomUser":
        """
        create_user

        :param self: Описание
        :param email: Описание
        :type email: str
        :param first_name: Описание
        :type first_name: str
        :param last_name: Описание
        :type last_name: str
        :param password: Описание
        :type password: str
        :param args: Описание
        :type args: tuple[Any, ...]
        :param kwargs: Описание
        :type kwargs: dict[Any, Any]
        """

        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> "CustomUser":
        """
        Docstring для create_superuser

        :param self: Описание
        :param email: Описание
        :type email: EmailField
        :param first_name: Описание
        :type first_name: str
        :param last_name: Описание
        :type last_name: str
        :param password: Описание
        :type password: str
        :param args: Описание
        :type args: tuple[Any, ...]
        :param kwargs: Описание
        :type kwargs: dict[Any, Any]
        """

        if not email:
            raise ValueError("Email is required")
        if not password:
            raise ValueError("Password is required")

        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user


FIRST_NAME_MAX_LENGTH = 50
LAST_NAME_MAX_LENGTH = 50


class CustomUser(
    AbstractBaseUser,
    PermissionsMixin,
    AbstractTimeStamptModel,
):
    email = EmailField(
        unique=True,
    )

    first_name = CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
    )
    last_name = CharField(
        max_length=LAST_NAME_MAX_LENGTH,
    )

    is_active = BooleanField(
        default=True,
    )
    is_staff = BooleanField(
        default=False,
    )

    date_joined = DateTimeField(
        auto_now_add=True,
    )

    avatar = ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "user"

    def __str__(self):
        return f"Email: {self.email}, Fullname: {self.first_name} {self.last_name}"
