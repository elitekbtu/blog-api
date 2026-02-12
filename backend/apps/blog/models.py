# Django modules
from django.db.models import (
    CharField,
    TextField,
    SlugField,
    TextChoices,
    ForeignKey,
    CASCADE,
    SET_NULL,
    ManyToManyField,
)

# Project modules
from apps.abstract.models import AbstractTimeStamptModel
from apps.users.models import CustomUser

# Constants
CATEGORY_MAX_NAME_LENGTH = 100
TAG_MAX_NAME_LENGTH = 50
POST_TITLE_MAX_LENGTH = 200


class Category(AbstractTimeStamptModel):
    """
    Blog post category.

    Fields:
        - name (CharField): Unique category name.
        - slug (SlugField): Unique URL-friendly identifier.

    Reverse relations:
        - posts: All posts in this category.
    """

    name = CharField(max_length=CATEGORY_MAX_NAME_LENGTH, unique=True)
    slug = SlugField(unique=True)


class Tag(AbstractTimeStamptModel):
    """
    Tag for grouping posts by topics.

    Fields:
        - name (CharField): Unique tag name.
        - slug (SlugField): Unique URL-friendly identifier.

    Reverse relations:
        - posts: All posts associated with this tag.
    """

    name = CharField(max_length=TAG_MAX_NAME_LENGTH, unique=True)
    slug = SlugField(unique=True)


class Post(AbstractTimeStamptModel):
    """
    Blog post created by a user.

    Fields:
        - author (ForeignKey): Post author.
        - title (CharField): Post title.
        - slug (SlugField): Unique URL-friendly identifier.
        - body (TextField): Post content.
        - category (ForeignKey): Optional post category.
        - tags (ManyToManyField): Tags assigned to the post.
        - status (CharField): Publication status (draft/published).

    Reverse relations:
        - comments: All comments related to this post.
    """

    class Status(TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    author = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name="posts",
    )

    title = CharField(max_length=POST_TITLE_MAX_LENGTH)
    slug = SlugField(unique=True)
    body = TextField()

    category = ForeignKey(
        Category,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )

    tags = ManyToManyField(
        Tag,
        blank=True,
        related_name="posts",
    )

    status = CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )


class Comment(AbstractTimeStamptModel):
    """
    Comment left by a user on a post.

    Fields:
        - post (ForeignKey): Related post.
        - author (ForeignKey): Comment author.
        - body (TextField): Comment content.

    Inherits:
        - created_at
        - updated_at
        - deleted_at
    """

    post = ForeignKey(
        Post,
        on_delete=CASCADE,
        related_name="comments",
    )

    author = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name="comments",
    )

    body = TextField()
