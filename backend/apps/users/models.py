# Python modules
from typing import Any

# Django modules
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

# Project modules
from backend.apps.abstract.models import AbstractTimeStamptModel


class CustomUserManager(BaseUserManager):
    """
    Custom UserManager for User Model

    Methods:
        - create_user: Create and save a User with the given email,
        first name, last name, and password.
        - create_superuser: Create and save a Superuser with the given email,
        first name, last name, and password.

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
        Create and save a User with the given email,
        first name, last name, and password.

        Args:
            email: Email of the user
            first_name: First name of the user
            last_name: Last name of the user
            password: Password of the user
            *args: tuple of positional arguments
            **kwargs: dict of keyword arguments
        Returns:
            CustomUser instance
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
        Create and save a Superuser with the given email,
        first name, last name, and password.

        Args:
            email: Email of the superuser
            first_name: First name of the superuser
            last_name: Last name of the superuser
            password: Password of the superuser
            *args: tuple of positional arguments
            **kwargs: dict of keyword arguments
        Returns:
            CustomUser instance
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
    """
    Custom User Model that
    extends AbstractBaseUser, PermissionsMixin,
    and AbstractTimeStamptModel

    Fields:
        - email: EmailField

        - first_name: CharField
        - last_name: CharField

        - is_active: BooleanField
        - is_staff: BooleanField

        - date_joined: DateTimeField
        - avatar: ImageField

        - created_at: DateTimeField
        - updated_at: DateTimeField
        - deleted_at: DateTimeField


    Methods:
        - __str__: Return a string representation of the user
    """

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
