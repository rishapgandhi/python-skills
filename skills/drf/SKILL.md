# Django REST Framework (DRF) Skill

> Load alongside `skills/django/SKILL.md` and all `skills/common/` files.

---

## Stack Additions (on top of Django)

| Layer | Library |
|---|---|
| REST Framework | djangorestframework 3.15+ |
| JWT Auth | `djangorestframework-simplejwt` |
| Filtering | `django-filter` |
| Throttling | DRF built-in |
| Schema / Docs | `drf-spectacular` (OpenAPI 3) |
| Pagination | DRF built-in + custom |

---

## Settings

```python
# config/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
    "EXCEPTION_HANDLER": "apps.core.exception_handler.custom_exception_handler",
}
```

---

## Serializer Standards

```python
# apps/users/serializers.py
from rest_framework import serializers
from apps.users.models import User

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user account."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "name", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already in use.")
        return value.lower()

    def create(self, validated_data: dict) -> User:
        from apps.users.services import UserService
        return UserService.create_user(**validated_data)


class UserResponseSerializer(serializers.ModelSerializer):
    """Read-only serializer for user responses."""

    class Meta:
        model = User
        fields = ["id", "public_id", "email", "name", "is_active", "created_at"]
        read_only_fields = fields
```

**Rule:** Use **separate serializers for read vs write**. Never use a single serializer for both.

---

## ViewSet Standards

```python
# apps/users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from apps.users.models import User
from apps.users.serializers import UserCreateSerializer, UserResponseSerializer

class UserViewSet(viewsets.ModelViewSet):
    """CRUD operations for user accounts."""

    queryset = User.objects.filter(is_active=True).order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserCreateSerializer
        return UserResponseSerializer

    def get_permissions(self):
        if self.action == "create":
            return []  # Public endpoint — allow registration
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def deactivate(self, request: Request, pk: int = None) -> Response:
        """Deactivate a user account."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## Custom Pagination

```python
# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "pages": self.page.paginator.num_pages,
            },
            "items": data,
        })
```

---

## Custom Exception Handler

```python
# apps/core/exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from apps.core.exceptions import AppBaseException

def custom_exception_handler(exc, context):
    if isinstance(exc, AppBaseException):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=_get_status(exc),
        )
    return exception_handler(exc, context)
```

---

## URL Router

```python
# apps/users/urls.py
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
urlpatterns = router.urls
```

---

## OpenAPI Docs with drf-spectacular

```python
# config/settings/base.py
SPECTACULAR_SETTINGS = {
    "TITLE": "My API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Decorate views:
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Create user",
    request=UserCreateSerializer,
    responses={201: UserResponseSerializer},
)
def create(self, request, *args, **kwargs):
    ...
```
