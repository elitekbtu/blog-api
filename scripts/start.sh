#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ENV_FILE="$ROOT_DIR/.env"
VENV_DIR="$ROOT_DIR/venv"
PYTHON_EXEC=""
CURRENT_STEP=""
SERVER_PID=""

SUPERUSER_EMAIL="admin@blogapi.local"
SUPERUSER_FIRST_NAME="Admin"
SUPERUSER_LAST_NAME="User"
SUPERUSER_PASSWORD="Admin12345!"

REQUIRED_ENV_VARS=(
  "BLOG_ENV_ID"
  "SECRET_KEY"
)

on_error() {
  local exit_code=$?
  echo "ERROR: Step failed: ${CURRENT_STEP}"
  exit "$exit_code"
}

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}

trap on_error ERR
trap cleanup EXIT

print_header() {
  echo
  echo "==> $1"
}

step() {
  CURRENT_STEP="$1"
  print_header "$CURRENT_STEP"
}

ensure_file_exists() {
  local path="$1"
  local label="$2"

  if [[ ! -f "$path" ]]; then
    echo "ERROR: ${label} not found at ${path}"
    exit 1
  fi
}

load_env_file() {
  ensure_file_exists "$ENV_FILE" ".env file"

  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
}

validate_required_env_vars() {
  local var_name
  local var_value

  for var_name in "${REQUIRED_ENV_VARS[@]}"; do
    var_value="${!var_name-}"
    if [[ -z "${var_value//[[:space:]]/}" ]]; then
      echo "Missing required environment variable: ${var_name}"
      exit 1
    fi
  done
}

setup_virtualenv_and_deps() {
  if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
  fi

  "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
  "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements/local.txt"
  PYTHON_EXEC="$VENV_DIR/bin/python"
}

run_manage_py() {
  local command="$1"
  shift

  (
    cd "$BACKEND_DIR"
    "$PYTHON_EXEC" manage.py "$command" "$@"
  )
}

ensure_superuser() {
  (
    cd "$BACKEND_DIR"
    "$PYTHON_EXEC" manage.py shell <<'PY'
from django.contrib.auth import get_user_model

User = get_user_model()
email = "admin@blogapi.local"
first_name = "Admin"
last_name = "User"
password = "Admin12345!"

user, created = User.objects.get_or_create(
    email=email,
    defaults={
        "first_name": first_name,
        "last_name": last_name,
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
)

changed = False
if not created:
    if user.first_name != first_name:
        user.first_name = first_name
        changed = True
    if user.last_name != last_name:
        user.last_name = last_name
        changed = True
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.is_superuser:
        user.is_superuser = True
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True

user.set_password(password)
user.save()

if created:
    print("Superuser created")
elif changed:
    print("Superuser updated")
else:
    print("Superuser already exists")
PY
  )
}

seed_database() {
  (
    cd "$BACKEND_DIR"
    "$PYTHON_EXEC" manage.py shell <<'PY'
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.blog.models import Category, Tag, Post, Comment

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

print(
    "Seed complete: "
    f"users={User.objects.count()}, "
    f"categories={Category.objects.count()}, "
    f"tags={Tag.objects.count()}, "
    f"posts={Post.objects.count()}, "
    f"comments={Comment.objects.count()}"
)
PY
  )
}

start_server() {
  (
    cd "$BACKEND_DIR"
    "$PYTHON_EXEC" manage.py runserver 0.0.0.0:8000
  ) &

  SERVER_PID=$!
  sleep 2

  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    wait "$SERVER_PID"
    echo "ERROR: Step failed: Start development server"
    exit 1
  fi
}

print_summary() {
  local host="http://127.0.0.1:8000"

  echo
  echo "Project is running"
  echo "API: ${host}/api/"
  echo "Swagger UI: ${host}/docs/schema/swagger-ui/"
  echo "ReDoc: ${host}/docs/schema/redoc/"
  echo "Admin panel: ${host}/admin/"
  echo
  echo "Superuser credentials"
  echo "Email: ${SUPERUSER_EMAIL}"
  echo "Password: ${SUPERUSER_PASSWORD}"
  echo
  echo "Press Ctrl+C to stop the server"
}

main() {
  step "Validate environment variables from .env"
  load_env_file
  validate_required_env_vars

  step "Create virtual environment and install dependencies"
  setup_virtualenv_and_deps

  step "Run migrations"
  run_manage_py migrate --noinput

  step "Collect static files"
  run_manage_py collectstatic --noinput

  step "Compile translation files"
  run_manage_py compilemessages

  step "Create superuser"
  ensure_superuser

  step "Seed database with test data"
  seed_database

  step "Start development server"
  start_server
  print_summary
  wait "$SERVER_PID"
}

main "$@"