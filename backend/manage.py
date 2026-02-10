#!/usr/bin/env python

# Pyhton modules
import os
import sys

# Project modules
from settings.conf import BLOG_ENV_ID, ENV_ID_POSSIBLE_OPTIONS


def main():
    """Run administrative tasks."""
    assert BLOG_ENV_ID in ENV_ID_POSSIBLE_OPTIONS, (
        f"Set correct BLOG_ENV_ID env var. Possible options: {ENV_ID_POSSIBLE_OPTIONS}"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{BLOG_ENV_ID}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
