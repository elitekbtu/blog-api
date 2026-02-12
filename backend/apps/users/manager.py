# Pythpon modules
from typing import Any, TYPE_CHECKING

# Django modules
from django.contrib.auth.models import (
    BaseUserManager,
)

# Project modules
if TYPE_CHECKING:
    from apps.users.models import CustomUser


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
