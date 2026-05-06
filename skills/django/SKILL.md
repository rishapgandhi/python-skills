# Django Skill

> Load this file when working on a Django project. Use alongside all `skills/common/` files.

---

## Stack

| Layer | Library |
|---|---|
| Framework | Django 5.x |
| ORM | Django ORM (built-in) |
| Migrations | Django migrations |
| Settings | `django-environ` or `pydantic-settings` |
| Static Files | WhiteNoise (prod) |
| Task Queue | Celery + Redis |
| Caching | django-redis |
| Admin | Django Admin (with `django-jazzmin` for UI) |

---

## Project Structure

```
myproject/
├── config/
│   ├── settings/
│   │   ├── base.py           ← Shared settings
│   │   ├── development.py    ← Dev overrides
│   │   └── production.py     ← Prod overrides
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py    ← (if using DRF)
│   │   ├── services.py
│   │   ├── repositories.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_services.py
│   └── core/
│       ├── models.py         ← Abstract base models
│       └── exceptions.py
├── manage.py
└── pyproject.toml
```

---

## Settings Pattern (Split by Environment)

```python
# config/settings/base.py
from pathlib import Path
import environ

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

DATABASES = {
    "default": env.db("DATABASE_URL")
}

INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local
    "apps.users",
    "apps.core",
]
```

---

## Abstract Base Model

```python
# apps/core/models.py
from django.db import models
import uuid

class TimeStampedModel(models.Model):
    """Abstract model that provides created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UUIDModel(models.Model):
    """Abstract model with UUID public identifier."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True
```

---

## Model Standards

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel, UUIDModel

class User(AbstractUser, TimeStampedModel, UUIDModel):
    """Custom user model — always use AbstractUser, never User directly."""

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"], name="ix_users_email"),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email
```

**Rule:** Always set `AUTH_USER_MODEL = "users.User"` in settings. Never use `from django.contrib.auth.models import User` directly in app code — always `get_user_model()`.

---

## Service Layer

Django views should be thin. Business logic goes in `services.py`:

```python
# apps/users/services.py
from django.db import transaction
from apps.users.models import User
from apps.core.exceptions import ConflictError

class UserService:
    @staticmethod
    @transaction.atomic
    def create_user(email: str, password: str, name: str) -> User:
        """Create and activate a new user account."""
        if User.objects.filter(email=email).exists():
            raise ConflictError(f"User with email '{email}' already exists.")
        user = User.objects.create_user(
            username=email, email=email, password=password, first_name=name
        )
        return user
```

---

## Admin Registration

```python
# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "name", "is_active", "created_at"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["email", "first_name"]
    ordering = ["-created_at"]
    readonly_fields = ["public_id", "created_at", "updated_at"]
```

---

## Django Tests

```python
# apps/users/tests/test_services.py
from django.test import TestCase
from apps.users.services import UserService
from apps.core.exceptions import ConflictError

class TestUserService(TestCase):
    def test_create_user_success(self):
        user = UserService.create_user(
            email="test@example.com", password="SecurePass1!", name="Test"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.is_active)

    def test_create_user_duplicate_email_raises_conflict(self):
        UserService.create_user(email="dup@example.com", password="Pass1!", name="A")
        with self.assertRaises(ConflictError):
            UserService.create_user(email="dup@example.com", password="Pass2!", name="B")
```

Use `TestCase` (wraps each test in a transaction, rolled back after). Use `TransactionTestCase` only when testing signals or raw transactions.

---

## Management Commands

```python
# apps/users/management/commands/seed_admin.py
from django.core.management.base import BaseCommand
from apps.users.models import User

class Command(BaseCommand):
    help = "Create default admin user for development"

    def handle(self, *args, **options):
        if not User.objects.filter(email="admin@example.com").exists():
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="changeme"
            )
            self.stdout.write(self.style.SUCCESS("Admin user created."))
```

---

## Fat Models & Chainable Custom Managers

Business logic belongs on the model or its manager — **not** in views or services.
Thin views, fat models. Small, named methods are easier to test and reuse.

```python
# apps/posts/models.py
import datetime
from django.db import models
from django.db.models import QuerySet


class PostQuerySet(QuerySet):
    """Chainable queryset methods — available on both manager and queryset."""

    def live(self) -> "PostQuerySet":
        """Filter to posts that are published and whose publish date has passed."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        return self.filter(date_published__lte=now, status=Post.Status.PUBLISHED)

    def by_author(self, author_id: int) -> "PostQuerySet":
        """Filter to posts by a specific author."""
        return self.filter(author_id=author_id)


class PostManager(models.Manager):
    """Default manager — returns PostQuerySet so all custom methods chain."""

    def get_queryset(self) -> PostQuerySet:
        return PostQuerySet(self.model, using=self._db)


class Post(models.Model):
    """Blog post with lifecycle management."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status, default=Status.DRAFT)
    author = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="posts"
    )
    date_published = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostManager()

    class Meta:
        ordering = ["-date_published"]
        indexes = [models.Index(fields=["status", "date_published"])]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        """Auto-set date_published when status transitions to PUBLISHED."""
        if self.status == self.Status.PUBLISHED and self.date_published is None:
            self.date_published = datetime.datetime.now(tz=datetime.timezone.utc)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return canonical URL for this post."""
        from django.urls import reverse
        return reverse("posts:detail", kwargs={"pk": self.pk})

    def is_live(self) -> bool:
        """Return True if this post is publicly visible right now."""
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        return (
            self.status == self.Status.PUBLISHED
            and self.date_published is not None
            and self.date_published <= now
        )
```

**Chaining works on both manager and queryset:**
```python
Post.objects.live()                          # direct on manager
Post.objects.by_author(5).live()             # chained on queryset
Post.objects.filter(title__icontains="AI").live()  # mixed
```

**Rule:** Custom logic that filters, annotates, or queries a model goes in a custom `QuerySet`
method. Never repeat the same `.filter(...)` call in two different views.

---

## Canonical Model Inner Class Ordering

All Django models follow this strict ordering inside the class body:

```python
class MyModel(models.Model):
    # 1. All database field definitions
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status)

    # 2. Custom manager attributes (replaces default `objects`)
    objects = MyModelManager()

    # 3. class Meta (one blank line after fields)
    class Meta:
        ordering = ["name"]
        verbose_name = "My Model"
        verbose_name_plural = "My Models"

    # 4. Python magic methods (__str__, __repr__, __eq__, etc.)
    def __str__(self) -> str:
        return self.name

    # 5. def save() override (if any)
    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

    # 6. def get_absolute_url() (if any)
    def get_absolute_url(self) -> str:
        ...

    # 7. All custom methods (business logic)
    def is_active(self) -> bool:
        ...
```

---

## Choices: Inline Constants vs TextChoices

**Preferred — `TextChoices` enum (Django 3.0+):**
```python
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.PENDING,
    )
```

**Acceptable — uppercase class attributes (legacy / external value constraints):**
```python
class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_CHOICES = {
        STATUS_PENDING: "Pending",
        STATUS_PROCESSING: "Processing",
    }

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
```

**Rules:**
- Always use `TextChoices` or `IntegerChoices` for new models.
- Choice constant names are **UPPER_CASE** — always.
- Never use bare strings for status comparisons: use `Order.Status.PENDING`, not `"pending"`.

---

## URLconf Rules

**Project URLconf (`config/urls.py`) — delegate, never define routes here:**
```python
# config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/posts/", include("apps.posts.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
]
```

**App URLconf (`apps/posts/urls.py`) — own all routes for that app:**
```python
# apps/posts/urls.py
from django.urls import path
from apps.posts import views

app_name = "posts"

urlpatterns = [
    path("", views.PostListView.as_view(), name="list"),
    path("<int:pk>/", views.PostDetailView.as_view(), name="detail"),
    path("create/", views.PostCreateView.as_view(), name="create"),
]
```

**Rules:**
- Never define application-specific routes in `config/urls.py`.
- Always set `app_name` for reversible URL namespaces (`reverse("posts:detail", ...)`).
- Separate URLconfs for separate environments if needed (e.g., `urls/dev.py` adds debug-toolbar).

---

## Template Naming & Organization

**Naming pattern:**
```
[app_name]/[model]_[function].html
```

| Template purpose | Path |
|---|---|
| List all contacts | `address_book/contact_list.html` |
| Detail view of contact | `address_book/contact_detail.html` |
| Create/update form | `address_book/contact_form.html` |
| Confirm delete | `address_book/contact_confirm_delete.html` |
| Partial / inclusion tag | `address_book/includes/contact_card.html` |

**Rules:**
- Keep all templates in the **project-level** `templates/` directory unless building a reusable app.
- Partials rendered by inclusion tags go in `templates/[app]/includes/`.
- Non-HTML templates use the appropriate extension (`.txt`, `.xml`, `.json`).

**Template style (Django template language):**
```django
{# This is a comment — allowed before extends #}
{% extends "base.html" %}

{% load i18n static %}

{% block content %}
<h1>{{ page.title }}</h1>

{% for item in items %}
    <p>{{ item.name }}</p>
{% endfor %}

{% if user.is_authenticated %}
    <a href="{% url 'logout' %}">{% trans "Logout" %}</a>
{% endif %}
{% endblock content %}
```

**Template rules:**
- `{% extends %}` must be the **first non-comment line**.
- `{% load %}` libraries in **alphabetical order**: `{% load i18n static %}` not `{% load static i18n %}`.
- Always name `{% endblock %}` tags: `{% endblock content %}` not `{% endblock %}`.
- Exactly **one space** inside `{{ variable }}` and `{% tag %}` — never `{{variable}}` or `{%tag%}`.
- No space around `.` for attribute access or `|` for filters: `{{ user.name|lower }}` not `{{ user.name | lower }}`.
- Never indent top-level `{% block %}` tags inside `{% extends %}` templates.

---

## Static Files & Media

```python
# config/settings/base.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Static files (CSS, JS, images — shipped with the project)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # collectstatic target
STATICFILES_DIRS = [BASE_DIR / "static"]  # source dirs

# --- Media files (user-generated uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"          # NEVER same dir as STATIC_ROOT
```

**Rules:**
- Always use `django.contrib.staticfiles` — never hardcode `/static/` paths in templates.
- In templates: `{% load static %}` then `{% static "css/main.css" %}`.
- `STATIC_ROOT` and `MEDIA_ROOT` must **never** be the same directory.
- In development, add `urlpatterns += static(settings.MEDIA_URL, ...)` to serve uploads locally.
- In production, serve static via WhiteNoise or a CDN — never Django itself.

```python
# config/urls.py — development media serving
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## `django.conf.settings` — Never Access at Module Import Time

Accessing `django.conf.settings` at module top-level breaks projects that configure
settings manually (e.g., in tests or CLI tools that call `settings.configure()`).

```python
# WRONG — evaluated at import time; breaks manual settings.configure()
from django.conf import settings
from django.urls import get_callable

default_view = get_callable(settings.FOO_VIEW)  # ❌ settings accessed at import
```

```python
# CORRECT — lazy wrapper evaluated only when called
from django.conf import settings
from django.utils.functional import lazy

def get_default_view():
    """Return the configured default view, resolved lazily."""
    from django.urls import get_callable
    return get_callable(settings.FOO_VIEW)   # ✅ accessed at call time
```

**Rule:** Any module-level code that reads from `django.conf.settings` must be wrapped
in a function, property, `lazy()`, or `LazyObject`. This is enforced by Django's own codebase.

---

## Internationalisation (i18n)

All user-visible strings must be wrapped for translation:

```python
# In Python code
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")

# In views / services
from django.utils.translation import gettext as _

def activate_user(user: User) -> None:
    if user.is_active:
        raise ValidationError(_("User is already active."))
```

**Rules:**
- Use `gettext_lazy` (`_`) in **model fields, Meta, forms, serializers** — evaluated lazily.
- Use `gettext` in **views and services** — evaluated immediately (request context available).
- **Never** use f-strings for strings that may need translation — format after wrapping:
  ```python
  # WRONG
  msg = f"Welcome, {user.name}!"

  # CORRECT
  msg = _("Welcome, %(name)s!") % {"name": user.name}
  ```
- Run `makemessages` and `compilemessages` in CI.

