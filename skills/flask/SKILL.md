# Flask Skill

> Load when working on a Flask project. Use alongside all `skills/common/` files.

---

## Stack

| Layer | Library |
|---|---|
| Framework | Flask 3.x |
| ORM | SQLAlchemy 2.x + Flask-SQLAlchemy |
| Migrations | Flask-Migrate (Alembic) |
| Validation | marshmallow or pydantic v2 |
| Auth | Flask-JWT-Extended |
| Settings | python-decouple / pydantic-settings |
| CLI | Click (built into Flask) |

---

## Project Structure

```
myapp/
├── app/
│   ├── __init__.py           ← App factory: create_app()
│   ├── extensions.py         ← Flask extension instances
│   ├── config.py
│   ├── models/
│   ├── schemas/              ← Marshmallow schemas
│   ├── repositories/
│   ├── services/
│   ├── blueprints/
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── tests/
│   │   └── auth/
│   │       ├── __init__.py
│   │       └── routes.py
│   └── errors.py             ← Error handlers
├── migrations/
├── tests/
├── .env.example
└── pyproject.toml
```

---

## App Factory

```python
# app/__init__.py
from flask import Flask
from app.extensions import db, migrate, jwt
from app.config import Config
from app.errors import register_error_handlers
from app.blueprints.users import users_bp
from app.blueprints.auth import auth_bp

def create_app(config_class: type = Config) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

    register_error_handlers(app)
    return app
```

---

## Extensions (Singleton Pattern)

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
```

---

## Blueprint + Route

```python
# app/blueprints/users/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import UserService
from app.schemas.user import UserCreateSchema, UserResponseSchema

users_bp = Blueprint("users", __name__)
create_schema = UserCreateSchema()
response_schema = UserResponseSchema()

@users_bp.route("/", methods=["POST"])
def create_user():
    """Create a new user account."""
    data = create_schema.load(request.json)  # validates + deserialises
    user = UserService.create_user(**data)
    return response_schema.dump(user), 201

@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    """Get a user by ID."""
    user = UserService.get_user(user_id)
    return response_schema.dump(user), 200
```

---

## Error Handlers

```python
# app/errors.py
from flask import Flask, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from app.core.exceptions import AppBaseException, NotFoundError, AuthorizationError

STATUS_MAP = {
    NotFoundError: 404,
    AuthorizationError: 403,
}

def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppBaseException)
    def handle_app_error(exc: AppBaseException):
        status = STATUS_MAP.get(type(exc), 500)
        return jsonify({"error": {"code": exc.code, "message": exc.message}}), status

    @app.errorhandler(MarshmallowValidationError)
    def handle_validation_error(exc: MarshmallowValidationError):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": exc.messages}}), 422

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Route not found."}}), 404
```

---

## Flask Testing

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db as _db
from app.config import TestConfig

@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# tests/test_users.py
def test_create_user_success(client):
    response = client.post("/api/v1/users/", json={
        "email": "test@example.com",
        "password": "SecurePass1!",
        "name": "Test User",
    })
    assert response.status_code == 201
    assert response.json["email"] == "test@example.com"
```

---

## Configuration — Class Hierarchy Pattern

Never put secrets or environment-specific values directly in code.
Use a class hierarchy with environment-variable switching:

```python
# app/config.py
import os
from pathlib import Path

class Config:
    """Base configuration — always version-controlled, no secrets."""
    TESTING: bool = False
    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Session cookie security (see Security section below)
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: int = 3600  # 1 hour

    # Celery (if used)
    CELERY: dict = {}

class DevelopmentConfig(Config):
    """Local dev — debug on, HTTP cookies ok."""
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False  # allows HTTP in dev

class TestingConfig(Config):
    """Test suite — in-memory DB, CSRF off."""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE: bool = False
    WTF_CSRF_ENABLED: bool = False

class ProductionConfig(Config):
    """Production — all secrets from env, never defaults."""
    SECRET_KEY: str = os.environ["SECRET_KEY"]          # must exist; crash if missing
    SQLALCHEMY_DATABASE_URI: str = os.environ["DATABASE_URL"]

# Map from FLASK_ENV / FLASK_CONFIG env var
config_map: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

def get_config() -> type[Config]:
    """Return config class based on FLASK_CONFIG env var."""
    env = os.environ.get("FLASK_CONFIG", "development")
    return config_map.get(env, DevelopmentConfig)
```

**Loading in factory:**
```python
# app/__init__.py
def create_app(config_class: type[Config] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # 1. Load class defaults
    app.config.from_object(config_class or get_config())

    # 2. Load env vars with FLASK_ prefix (overrides class defaults)
    app.config.from_prefixed_env()  # FLASK_SECRET_KEY → config["SECRET_KEY"]

    # 3. (Optional) load instance/local override file — not in version control
    app.config.from_pyfile("config.py", silent=True)
    ...
```

**Rules:**
- `from_prefixed_env()` reads all `FLASK_*` env vars and maps them into config. Use this in production.
- Never access `app.config` at module import time — only inside factory functions or `before_request`.
- Load config **before** calling `extension.init_app(app)` so extensions see config at startup.
- `TestingConfig` passes in the factory: `create_app(TestingConfig)` — never uses env files.

---

## Application Context & `g`

The `g` object stores **request-scoped** data (resources created and torn down per request).
It is **not** a cross-request cache — data on `g` dies when the request ends.

```python
# app/database.py
from flask import g
from app.extensions import db

def get_db_connection():
    """Return the same DB connection for the entire request, create if missing."""
    if "db_conn" not in g:
        g.db_conn = db.engine.connect()
    return g.db_conn

# Register teardown — always closes the connection even if view raised an exception
def teardown_db(exception: BaseException | None) -> None:
    """Close DB connection when app context pops (end of request or CLI command)."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()

# Register in factory:
# app.teardown_appcontext(teardown_db)
```

**Pattern — get_X / teardown_X:**
```python
# Any resource that should be created once per request follows this pattern:
# 1. get_X() — creates and caches on g if not already there
# 2. teardown_X() — closes/releases; registered with @app.teardown_appcontext

from werkzeug.local import LocalProxy
db_conn = LocalProxy(get_db_connection)  # access db_conn like a normal object
```

**Rules:**
- Use `g` for request-scoped resources (DB connections, current user cache, feature flags).
- Use `session` for data that must persist across requests (user login state).
- Use `current_app.extensions["my_ext"]` for app-level shared state.
- `g` is reset fresh for every request and every CLI command invocation.

---

## Request Lifecycle & Hook Ordering

```
before_request()           ← runs before every view; returning a value short-circuits the view
  │
  ▼
view function()            ← the matched route handler
  │
  ▼
after_request(response)    ← runs after every successful view; must return a response
  │
  ▼
teardown_request(exc)      ← always runs, even after errors; receives exception or None
  │
  ▼ (context pops)
teardown_appcontext(exc)   ← always runs when context is removed (end of request + CLI)
```

```python
# app/blueprints/auth/routes.py
from flask import g, request, jsonify, abort
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

@auth_bp.before_request
def load_authenticated_user() -> None:
    """Attach the current user to g before every request in this blueprint."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    g.current_user = AuthService.get_user_from_token(token) if token else None

@auth_bp.after_request
def add_security_headers(response):
    """Attach security headers to every response from this blueprint."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
```

**Rules:**
- `before_request` returning a value **skips** the view entirely — use for auth checks.
- `after_request` **must always return** a response object — returning `None` is a bug.
- `teardown_request` receives the exception (or `None`) — use for resource cleanup, NOT for error responses.
- Blueprint hooks only run for requests that match that blueprint's routes.

---

## Class-Based Views (MethodView) — REST APIs

`MethodView` dispatches HTTP methods to same-named class methods. Best for resource APIs:

```python
# app/blueprints/users/views.py
from flask import request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from app.services.user_service import UserService
from app.schemas.user import UserCreateSchema, UserUpdateSchema, UserResponseSchema

response_schema = UserResponseSchema()

class UserItemView(MethodView):
    """Single user resource — GET, PATCH, DELETE."""

    decorators = [jwt_required()]  # applied to all methods automatically

    def get(self, user_id: int):
        """Return a single user."""
        user = UserService.get_or_404(user_id)
        return jsonify(response_schema.dump(user))

    def patch(self, user_id: int):
        """Partially update a user."""
        schema = UserUpdateSchema()
        data = schema.load(request.json or {})
        user = UserService.update(user_id, **data)
        return jsonify(response_schema.dump(user))

    def delete(self, user_id: int):
        """Delete a user."""
        UserService.delete(user_id)
        return "", 204


class UserListView(MethodView):
    """User collection — GET (list), POST (create)."""

    def get(self):
        """List all users."""
        users = UserService.list_all()
        return jsonify(response_schema.dump(users, many=True))

    @jwt_required()
    def post(self):
        """Create a new user."""
        schema = UserCreateSchema()
        data = schema.load(request.json or {})
        user = UserService.create(**data)
        return jsonify(response_schema.dump(user)), 201


# Register in factory or blueprint:
def register_user_views(app_or_bp) -> None:
    user_item = UserItemView.as_view("user-item")
    user_list = UserListView.as_view("user-list")
    app_or_bp.add_url_rule("/users/<int:user_id>", view_func=user_item)
    app_or_bp.add_url_rule("/users/", view_func=user_list)
```

**Rule:** Set `init_every_request = False` when the view stores state in `__init__` that is
safe to reuse across requests (e.g. a schema instance). The default creates a new instance
per request, which is safer but slower.

---

## Custom API Error Classes

```python
# app/errors.py
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
import werkzeug.exceptions


class APIError(Exception):
    """Base class for all application API errors."""
    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None, payload: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> dict:
        return {"message": self.message, "code": type(self).__name__, **self.payload}


class NotFoundError(APIError):
    status_code = 404

class ConflictError(APIError):
    status_code = 409

class ValidationError(APIError):
    status_code = 422

class UnauthorizedError(APIError):
    status_code = 401


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers on the app."""

    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        # Return JSON for API routes, HTML for everything else
        if request.path.startswith("/api/"):
            return jsonify({"message": exc.description, "code": exc.name}), exc.code
        return exc  # default HTML response

    @app.errorhandler(404)
    def handle_404(exc):
        if request.path.startswith("/api/"):
            return jsonify({"message": "Resource not found.", "code": "NOT_FOUND"}), 404
        return jsonify({"message": "Not found."}), 404

    @app.errorhandler(405)
    def handle_405(exc):
        # 404 and 405 at blueprint level only fire for that blueprint's routes.
        # Register here at app level for global coverage.
        return jsonify({"message": "Method not allowed.", "code": "METHOD_NOT_ALLOWED"}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        return jsonify({"message": "Internal server error.", "code": "SERVER_ERROR"}), 500
```

**Blueprint 404/405 caveat:** Blueprints do NOT own the entire URL space — `404` and `405`
errors from URLs that don't match any blueprint route are never dispatched to a blueprint-level
error handler. Always register `404` and `405` handlers at the **application level**.

---

## View Decorators

```python
# app/decorators.py
from functools import wraps
from typing import Callable
from flask import g, request, redirect, url_for, jsonify
from app.core.exceptions import UnauthorizedError


def login_required(f: Callable) -> Callable:
    """Redirect unauthenticated users to login; for API routes raise 401."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.current_user is None:
            if request.path.startswith("/api/"):
                raise UnauthorizedError("Authentication required.")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def roles_required(*roles: str) -> Callable:
    """Allow only users with one of the given roles."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.current_user is None or g.current_user.role not in roles:
                raise UnauthorizedError("Insufficient permissions.")
            return f(*args, **kwargs)
        return decorated
    return decorator
```

**Usage:**
```python
@users_bp.route("/admin-panel")
@login_required
@roles_required("admin", "superuser")
def admin_panel():
    ...
```

**Rules:**
- Always use `@functools.wraps(f)` — preserves function name, docstring, and signature.
- `@app.route` must be the **outermost** decorator; custom decorators go **inside** it.
- For `MethodView`, use the `decorators` class attribute instead of stacking on each method.

---

## Security Headers & Cookie Settings

Set these in `after_request` or via Flask-Talisman. All production apps must include:

```python
# app/__init__.py
def register_security_headers(app: Flask) -> None:
    """Attach security response headers to every response."""

    @app.after_request
    def set_security_headers(response):
        # Prevent MIME-type sniffing — stops XSS via uploaded files
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking — only allow framing from same origin
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # Force HTTPS for 1 year (only set in production — omit in dev)
        if not app.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # Content Security Policy — restrict resource origins
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
```

**Session cookie hardening (set in `Config`):**
```python
app.config.update(
    SESSION_COOKIE_SECURE=True,       # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,     # JS cannot read cookie
    SESSION_COOKIE_SAMESITE="Lax",   # blocks cross-site POST forgery
    PERMANENT_SESSION_LIFETIME=3600, # expire after 1 hour
)
```

**Handling sessions correctly:**
```python
@auth_bp.route("/login", methods=["POST"])
def login():
    user = AuthService.authenticate(request.form["username"], request.form["password"])
    if user is None:
        abort(401)

    session.clear()              # ✅ always clear before setting — prevents session fixation
    session["user_id"] = user.id
    session.permanent = True     # respects PERMANENT_SESSION_LIFETIME
    return redirect(url_for("index"))
```

**XSS prevention in templates:**
```jinja2
{# Jinja2 auto-escapes {{ value }} — safe for HTML content #}
<input value="{{ value }}">      {# ✅ attribute MUST be quoted #}

{# NEVER: #}
<input value={{ value }}>        {# ❌ attribute injection vulnerability #}

{# For href — set CSP; Jinja cannot protect against javascript: URIs #}
<a href="{{ url_for('profile', user_id=user.id) }}">Profile</a>  {# ✅ always use url_for #}
```

**CSRF protection:**
Flask does NOT include built-in CSRF protection. Use **Flask-WTF** or implement token-based
protection for any state-mutating endpoint that accepts form submissions:
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
csrf.init_app(app)  # protects all POST/PUT/PATCH/DELETE form endpoints
```

---

## Celery Integration

```python
# app/celery_utils.py
from celery import Celery, Task
from flask import Flask


def celery_init_app(app: Flask) -> Celery:
    """Create and configure a Celery app that runs tasks inside a Flask app context."""

    class FlaskTask(Task):
        """Task subclass that wraps execution in a Flask application context."""

        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
```

**Factory integration:**
```python
# app/__init__.py
def create_app(config_class: type = ProductionConfig) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Celery config lives under the CELERY key in Flask config
    app.config.setdefault("CELERY", {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
        "task_ignore_result": True,
    })

    celery_init_app(app)
    ...
    return app
```

**Defining tasks:**
```python
# app/tasks/email_tasks.py
from celery import shared_task
from app.services.email_service import EmailService

@shared_task(ignore_result=False)
def send_welcome_email(user_id: int) -> dict:
    """Send welcome email to new user. Runs in a Flask app context automatically."""
    EmailService.send_welcome(user_id)
    return {"status": "sent", "user_id": user_id}
```

**Running workers:**
```bash
# Worker
celery -A "app:celery_app" worker --loglevel INFO

# Scheduler (beat)
celery -A "app:celery_app" beat --loglevel INFO
```

**Rule:** `shared_task` works without importing a specific Celery instance — it uses the default
set by `celery_app.set_default()`. This avoids circular imports between tasks and the factory.

---

## Async Views (Flask 2.0+)

Flask supports `async def` views when installed with the `async` extra:

```bash
pip install flask[async]
```

```python
@app.route("/data")
async def get_data():
    """Fetch from multiple async sources concurrently."""
    import asyncio
    results = await asyncio.gather(
        fetch_from_service_a(),
        fetch_from_service_b(),
    )
    return jsonify({"a": results[0], "b": results[1]})
```

**When async is useful:**
- Multiple concurrent I/O calls within a single view (parallel API calls, parallel DB queries).
- Using async-native libraries (httpx, aiohttp, asyncpg).

**When NOT to use async:**
- CPU-bound work — async provides no benefit, use Celery workers instead.
- If most of your code is async — use **Quart** (async-first Flask reimplementation on ASGI)
  instead. Flask async runs each request in its own thread-scoped event loop, so it doesn't
  improve request concurrency the way a true ASGI server does.

**Critical async limitation:**
```python
# WRONG — background tasks spawned with asyncio.create_task are cancelled
# when the view function returns
@app.route("/fire-and-forget")
async def bad_background():
    asyncio.create_task(long_running())  # ❌ cancelled immediately
    return "ok"

# CORRECT — use Celery for fire-and-forget work
@app.route("/fire-and-forget")
def good_background():
    long_running_task.delay()           # ✅ runs in Celery worker process
    return "ok"
```

---

## Flask Testing — Complete Patterns

### Test Client & Fixtures

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db as _db
from app.config import TestingConfig

@pytest.fixture(scope="session")
def app():
    """App instance for the test session — one DB creation per session."""
    _app = create_app(TestingConfig)
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()

@pytest.fixture
def client(app):
    """Fresh test client per test."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing Click commands."""
    return app.test_cli_runner()
```

### Session Access & Mutation

```python
from flask import session

def test_login_sets_session(client):
    """Successful login stores user_id in session."""
    response = client.post("/auth/login", data={
        "username": "alice", "password": "correct"
    })
    assert response.status_code == 302  # redirect after login

    with client:
        client.get("/")                 # any request to activate context
        assert session["user_id"] == 1  # session readable inside `with client`

def test_pre_seed_session(client):
    """Seed session directly to bypass login flow."""
    with client.session_transaction() as sess:
        sess["user_id"] = 42            # set before making request

    response = client.get("/users/me")
    assert response.json["id"] == 42
```

### Redirect Following & Context

```python
def test_logout_redirects_to_index(client):
    response = client.get("/auth/logout", follow_redirects=True)
    # With follow_redirects=True, response is the final non-redirect response
    assert response.status_code == 200
    assert b"Logged out" in response.data
    assert len(response.history) == 1   # one redirect in the chain

def test_function_using_request(app):
    """Test a helper that accesses `request` directly without making an HTTP call."""
    with app.test_request_context("/users/edit?format=json", method="POST"):
        from app.helpers import parse_format
        assert parse_format() == "json"
```

### CLI Command Testing

```python
@app.cli.command("create-admin")
@click.option("--email", required=True)
def create_admin(email: str) -> None:
    """Create an admin user."""
    UserService.create_admin(email)
    click.echo(f"Admin {email} created.")

def test_create_admin_command(runner):
    result = runner.invoke(args=["create-admin", "--email", "admin@example.com"])
    assert result.exit_code == 0
    assert "Admin admin@example.com created" in result.output
```

### App Context in Tests

```python
def test_db_record_created(app):
    """Test that a model was actually saved — needs app context for ORM access."""
    with app.app_context():
        from app.models import User
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.is_active is True
```

