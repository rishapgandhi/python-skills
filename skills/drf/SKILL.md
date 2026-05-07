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

### When to use which ViewSet

| Class | Use when |
|-------|----------|
| `ModelViewSet` | Full CRUD on a model |
| `ReadOnlyModelViewSet` | List + retrieve only (public catalogs) |
| `GenericViewSet` + mixins | Selective actions (e.g., create + list, no update/delete) |
| `ViewSet` | Non-model logic (aggregations, external API proxies) |

### Standard ModelViewSet

```python
# apps/users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from apps.users.models import User
from apps.users.serializers import UserCreateSerializer, UserUpdateSerializer, UserResponseSerializer
from apps.users.permissions import IsOwnerOrAdmin
from apps.users.filters import UserFilterSet

class UserViewSet(viewsets.ModelViewSet):
    """CRUD operations for user accounts."""

    queryset = User.objects.filter(is_active=True).order_by("-created_at")
    http_method_names = ["get", "post", "put", "patch", "delete"]
    filterset_class = UserFilterSet
    search_fields = ["email", "name"]
    ordering_fields = ["created_at", "name"]

    def get_serializer_class(self):
        match self.action:
            case "create":
                return UserCreateSerializer
            case "update" | "partial_update":
                return UserUpdateSerializer
            case _:
                return UserResponseSerializer

    def get_permissions(self):
        if self.action == "create":
            return []  # Public registration
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Delegate creation to service layer."""
        from apps.users.services import UserService
        UserService.create_user(**serializer.validated_data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request: Request, pk: int = None) -> Response:
        """Deactivate a user account."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

### Selective Mixins (no full CRUD)

```python
from rest_framework import viewsets, mixins

class InvitationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Invitations: create, list, delete. No update."""
    ...
```

---

## Nested Serializers

### Read — nested representation

```python
class CommentSerializer(serializers.ModelSerializer):
    author = UserResponseSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "body", "author", "created_at"]


class PostDetailSerializer(serializers.ModelSerializer):
    """Nested read: includes comments and author."""
    author = UserResponseSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "body", "author", "comments", "comment_count", "created_at"]
```

### Write — accept IDs, not nested objects

```python
class PostCreateSerializer(serializers.ModelSerializer):
    """Write: accept author_id, not nested author object."""
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="author",
    )

    class Meta:
        model = Post
        fields = ["title", "body", "author_id"]
```

### Writable Nested (when needed)

```python
class OrderCreateSerializer(serializers.ModelSerializer):
    """Writable nested: create order + line items in one request."""
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["customer_id", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item) for item in items_data
        ])
        return order
```

**Rule:** Writable nested serializers must override `create()` and/or `update()` explicitly. DRF does not handle nested writes automatically.

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

## Permissions

### Built-in Permission Classes

| Class | Use when |
|-------|----------|
| `IsAuthenticated` | Default for all endpoints |
| `IsAdminUser` | Admin-only operations |
| `AllowAny` | Public endpoints (registration, password reset) |
| `IsAuthenticatedOrReadOnly` | Public read, authenticated write |

### Custom Permissions

```python
# apps/core/permissions.py
from rest_framework.permissions import BasePermission

class IsOwnerOrAdmin(BasePermission):
    """Allow access only to the object owner or admin users."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_staff:
            return True
        return obj.user_id == request.user.id


class IsOrganizationMember(BasePermission):
    """Restrict access to members of the same organization."""

    def has_permission(self, request, view) -> bool:
        org_id = view.kwargs.get("org_id")
        return request.user.organizations.filter(id=org_id).exists()


class HasAPIScope(BasePermission):
    """Check JWT token has required scope (for machine-to-machine auth)."""

    required_scope = ""

    def has_permission(self, request, view) -> bool:
        token_scopes = getattr(request.auth, "payload", {}).get("scopes", [])
        return self.required_scope in token_scopes
```

### Permission Composition

```python
# Combine with AND (tuple) or OR (custom)
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrganizationMember]  # AND — both must pass

# OR logic requires a helper:
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
```

---

## Throttling

### Configuration

```python
# config/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",       # Custom scope for auth endpoints
        "export": "10/hour",       # Heavy operations
    },
}
```

### Per-View Throttling

```python
from rest_framework.throttling import ScopedRateThrottle

class LoginView(APIView):
    """Rate-limited login to prevent brute force."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        ...


class ExportView(APIView):
    """Heavy export — limited to 10/hour."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "export"

    def get(self, request):
        ...
```

### Custom Throttle (burst protection)

```python
from rest_framework.throttling import SimpleRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    """Short burst limit: 10 requests per 10 seconds."""
    scope = "burst"
    rate = "10/10s"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f"throttle_burst_{request.user.id}"
        return f"throttle_burst_{self.get_ident(request)}"
```

---

## Filtering

```python
# apps/users/filters.py
import django_filters
from apps.users.models import User

class UserFilterSet(django_filters.FilterSet):
    """Filterable fields for user list endpoint."""
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    role = django_filters.CharFilter(field_name="role", lookup_expr="exact")

    class Meta:
        model = User
        fields = ["is_active", "role"]
```

**Rule:** Never expose raw model fields directly. Use a FilterSet to whitelist allowed filters.

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

---

## Testing DRF Views

```python
# apps/users/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from apps.users.factories import UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client) -> APIClient:
    user = UserFactory()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


class TestUserViewSet:
    def test_list_users_requires_auth(self, api_client):
        response = api_client.get("/api/v1/users/")
        assert response.status_code == 401

    def test_list_users_returns_paginated(self, authenticated_client):
        UserFactory.create_batch(25)
        response = authenticated_client.get("/api/v1/users/")
        assert response.status_code == 200
        assert "pagination" in response.data
        assert response.data["pagination"]["page_size"] == 20

    def test_create_user_returns_201(self, api_client):
        payload = {"email": "new@example.com", "name": "New User", "password": "securepass123"}
        response = api_client.post("/api/v1/users/", payload, format="json")
        assert response.status_code == 201

    def test_owner_can_update_own_profile(self, authenticated_client):
        response = authenticated_client.patch(
            f"/api/v1/users/{authenticated_client.user.id}/",
            {"name": "Updated"},
            format="json",
        )
        assert response.status_code == 200

    def test_non_owner_cannot_update_other_profile(self, authenticated_client):
        other = UserFactory()
        response = authenticated_client.patch(
            f"/api/v1/users/{other.id}/",
            {"name": "Hacked"},
            format="json",
        )
        assert response.status_code == 403
```

---

## Rules Summary

| Rule | Rationale |
|------|-----------|
| Separate read/write serializers | Prevents accidental field exposure |
| Never accept nested objects for write — use IDs | Simpler validation, avoids ambiguity |
| Override `get_serializer_class()` per action | Clean action-specific schemas |
| Always set `http_method_names` on ViewSets | Prevent unintended HTTP methods |
| Use `select_related`/`prefetch_related` in `get_queryset()` | Prevent N+1 queries |
| Custom permissions per action via `get_permissions()` | Granular access control |
| Rate-limit auth endpoints aggressively | Prevent brute force |
| Use `drf-spectacular` for docs — never manual OpenAPI | Single source of truth |
| Test every permission boundary | Security regressions are silent |
