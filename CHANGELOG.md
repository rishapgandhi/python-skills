# Changelog

All notable changes to `python-agent-standards` are documented here.

---

## [3.0.0] — May 2026

### Added — skills/django/SKILL.md
- Fat models and chainable custom QuerySet managers (`PostQuerySet`, `PostManager`)
- Canonical model inner-class ordering (fields → managers → Meta → `__str__` → `save` → `get_absolute_url` → custom methods)
- `TextChoices` vs inline constant patterns with rules
- URLconf delegation rules and `app_name` namespace guidance
- Template naming conventions (`[app]/[model]_[function].html`, `includes/` for partials)
- Template style rules (quoted attributes, `{% endblock name %}`, alphabetical `{% load %}`)
- Static files vs media files setup (`STATIC_ROOT` vs `MEDIA_ROOT`)
- `django.conf.settings` lazy access rule (never read at module import time)
- Internationalisation patterns (`gettext_lazy` vs `gettext`, no f-strings for translatable strings)

### Added — skills/common/code-style.md
- §13.5 expanded: f-string expression constraints (plain access only, no function calls inside `{}`)
- §13.6 (new): NOQA/type-ignore/pylint suppression specificity rules
- §12.11: Late binding closures — the loop-lambda gotcha and both fixes
- §12.12: Python idioms reference (unpacking, `__` throwaway, list multiplication trap, string join, set membership)
- §12.13: Function argument design rules (positional vs keyword vs *args vs **kwargs)
- §12.14: Pure functions and minimising side effects with before/after example
- §12.15: Variable naming under dynamic typing — avoid same-name for different types

### Added — skills/common/testing.md
- Section 0: Nine testing principles from the Hitchhiker's Guide (one-thing, independence, descriptive names, speed, debug-via-test, etc.)
- Section 10: Django-specific testing (`TestCase` vs `TransactionTestCase` vs `SimpleTestCase`)
- Section 10.2: Preferred Django assertion methods (`assertRaisesMessage`, `assertIs(x, True)`)
- Section 10.3: Conditional version pragmas (`# pragma: only py>=3.11`, `# pragma: django>=4.2 branch`)
- Section 12: Assert method selection guide (full reference table)
- Section 13: Skip decorators and `@expectedFailure` patterns
- Section 14: Fixture lifecycle (`setUp → addCleanup → setUpClass → setUpModule`)
- Section 15: `subTest` context manager for iteration-based testing
- Section 16: `IsolatedAsyncioTestCase` for async tests

### Added — skills/common/folder-structure.md
- Section 10: Module and package design rules (import style table, `__init__.py` patterns, project pitfalls table, pure functions vs classes decision guide)

### Added — skills/flask/SKILL.md
- Configuration class hierarchy (`Config → DevelopmentConfig / TestingConfig / ProductionConfig`)
- `from_prefixed_env()` loading pattern
- Application context and `g` object (`get_X / teardown_X` pattern, `LocalProxy`)
- Request lifecycle hook ordering (`before_request → view → after_request → teardown_request → teardown_appcontext`)
- `MethodView` for REST APIs with `decorators` class attribute
- Custom API error classes (`APIError` hierarchy, `to_dict()` pattern)
- Blueprint 404/405 caveat (must be registered at app level)
- View decorators (`login_required`, `roles_required`) with `@functools.wraps` rule
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`)
- Session hardening (`session.clear()` before setting, `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE`)
- Celery integration (`FlaskTask` subclass, `celery_init_app()`, `shared_task`)
- Async views — when useful, when not, `asyncio.create_task` cancellation trap
- Testing patterns (session seeding, redirect following, `test_request_context`, CLI runner)

### Added — skills/common/testing.md (unittest PDF)
- Full assert method selection guide with decision tables
- Skip decorators (`@skip`, `@skipIf`, `@skipUnless`, `@expectedFailure`)
- Fixture lifecycle hierarchy
- `addCleanup` over `tearDown` guidance
- `subTest` context manager
- `IsolatedAsyncioTestCase` for async

---

## [2.0.0] — May 2026 (initial release)

- Core skill files: code-style, folder-structure, error-handling, logging, security, testing, db-design
- Framework skills: FastAPI, Django, DRF, Flask
- Cursor MDC rules: python-core, python-fastapi, python-django, python-testing, python-security
- Claude Code slash commands: /load-skill, /new-endpoint, /review, /add-tests, /migrate
- QA agent definition
- Developer onboarding guide
- New skills: performance.md, llm-patterns.md
