from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.blog.models import Category, Comment, Post, Tag


class Command(BaseCommand):
    help = "Populate the database with demo users, taxonomy, posts, and comments."

    def handle(self, *args, **options):
        User = get_user_model()

        users_payload = [
            ("alice@example.com", "Alice", "Smith", "en", "UTC"),
            ("bob@example.com", "Bob", "Johnson", "ru", "Asia/Almaty"),
            ("carol@example.com", "Carol", "Lee", "kk", "Asia/Almaty"),
            ("dmitri@example.com", "Dmitri", "Petrov", "ru", "Europe/Moscow"),
            ("aigerim@example.com", "Aigerim", "Sultan", "kk", "Asia/Almaty"),
            ("maria@example.com", "Maria", "Ivanova", "ru", "UTC"),
            ("nurlan@example.com", "Nurlan", "Bek", "kk", "Asia/Qyzylorda"),
            ("john@example.com", "John", "Doe", "en", "UTC"),
        ]

        users = []
        for email, first_name, last_name, preferred_language, timezone in users_payload:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "preferred_language": preferred_language,
                    "timezone": timezone,
                    "is_active": True,
                },
            )
            user.first_name = first_name
            user.last_name = last_name
            user.preferred_language = preferred_language
            user.timezone = timezone
            user.is_active = True
            user.set_password("User12345!")
            user.save()
            users.append(user)

        categories_payload = [
            ("Backend", "Бэкенд", "Бэкенд"),
            ("Frontend", "Фронтенд", "Фронтенд"),
            ("DevOps", "ДевОпс", "DevOps"),
            ("Data Science", "Наука о данных", "Деректер ғылымы"),
            ("Mobile", "Мобильная разработка", "Мобильді даму"),
            ("Security", "Безопасность", "Қауіпсіздік"),
        ]

        categories = []
        for en_name, ru_name, kk_name in categories_payload:
            slug = slugify(en_name)
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": en_name,
                    "name_ru": ru_name,
                    "name_kk": kk_name,
                },
            )
            category.name = en_name
            category.name_ru = ru_name
            category.name_kk = kk_name
            category.save()
            categories.append(category)

        tag_names = [
            "django",
            "python",
            "api",
            "testing",
            "docker",
            "redis",
            "performance",
            "security",
            "i18n",
            "pagination",
            "auth",
            "ci-cd",
            "sql",
            "monitoring",
            "observability",
        ]

        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name},
            )
            tag.name = name
            tag.save()
            tags.append(tag)

        target_posts = 140
        posts = []
        for idx in range(1, target_posts + 1):
            author = users[idx % len(users)]
            category = categories[idx % len(categories)]
            status = Post.Status.PUBLISHED if idx % 4 != 0 else Post.Status.DRAFT
            title = f"Sample Post {idx:03d}"

            post, _ = Post.objects.get_or_create(
                title=title,
                author=author,
                defaults={
                    "body": (
                        f"This is the body for {title}. "
                        "It contains enough text to test list/detail views, "
                        "translation behavior and filtering scenarios."
                    ),
                    "category": category,
                    "status": status,
                },
            )

            post.body = (
                f"This is the body for {title}. "
                "It contains enough text to test list/detail views, "
                "translation behavior and filtering scenarios."
            )
            post.category = category
            post.status = status
            post.save()

            selected_tags = [
                tags[idx % len(tags)],
                tags[(idx + 3) % len(tags)],
                tags[(idx + 7) % len(tags)],
            ]
            post.tags.set(selected_tags)
            posts.append(post)

        for idx, post in enumerate(posts[:110], start=1):
            commenter_a = users[(idx + 1) % len(users)]
            commenter_b = users[(idx + 2) % len(users)]

            body_a = f"Insightful comment A on {post.title}"
            body_b = f"Insightful comment B on {post.title}"

            Comment.objects.get_or_create(post=post, author=commenter_a, body=body_a)
            Comment.objects.get_or_create(post=post, author=commenter_b, body=body_b)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: "
                f"users={User.objects.count()}, "
                f"categories={Category.objects.count()}, "
                f"tags={Tag.objects.count()}, "
                f"posts={Post.objects.count()}, "
                f"comments={Comment.objects.count()}"
            )
        )
