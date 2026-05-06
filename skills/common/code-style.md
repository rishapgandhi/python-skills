# Python Code Style & Conventions
# Enterprise Standard — PEP 8 Complete, Version-Aware, 18+ Years Depth

> Authority: PEP 8 (active, revised 2025-04-04), PEP 257, PEP 484, PEP 526, PEP 604, PEP 695.
> Applies to: Python 3.8 through 3.13+. Version deltas called out explicitly.
> This skill supersedes any prior code-style guidance. Load first, always.

---

## PRIME DIRECTIVE

"A Foolish Consistency is the Hobgoblin of Little Minds" — Guido van Rossum, PEP 8.

Rules have priorities:
1. Correctness — broken code that passes style is unacceptable.
2. Consistency within a module/function — most important scope.
3. Consistency within a project — second.
4. This style guide — third.

Know when to deviate. Document why with a comment when you do.
Never break backwards compatibility just to comply with a style rule.

---

## 1. TOOLCHAIN

| Tool | Role | Min Version |
|------|------|-------------|
| Ruff | Linter + formatter | 0.4+ |
| mypy | Static type checker | 1.8+ |
| pytest | Test runner | 7.4+ |
| pre-commit | Git hook runner | 3.6+ |

Black was the prior standard. Ruff's formatter is Black-compatible and faster.
Never use both Ruff formatter AND Black in the same project.

---

## 2. CODE LAYOUT

### 2.1 Indentation

4 spaces per level. No tabs. Never mix.

```python
# Correct — aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Correct — hanging indent with extra 4 spaces (distinguishes from body)
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

# Correct — hanging indent, simple form (most used)
foo = long_function_name(
    var_one, var_two,
    var_three, var_four,
)

# WRONG — args on first line without vertical alignment
foo = long_function_name(var_one, var_two,
    var_three, var_four)

# WRONG — indentation indistinguishable from body
def long_function_name(
    var_one, var_two,
    var_four):
    print(var_one)
```

Multiline if — three accepted forms (choose one per project):

```python
# Form 1
if (this_is_one_thing and
    that_is_another_thing):
    do_something()

# Form 2 — with comment for visual distinction
if (this_is_one_thing and
    that_is_another_thing):
    # Both conditions true; proceed.
    do_something()

# Form 3 — extra indent on continuation (clearest)
if (this_is_one_thing
        and that_is_another_thing):
    do_something()
```

Closing delimiter — two accepted forms (choose one per project):

```python
# Form A — under last item's first non-whitespace char
my_list = [
    1, 2, 3,
    4, 5, 6,
    ]

# Form B — under line that starts the construct (Ruff default)
my_list = [
    1, 2, 3,
    4, 5, 6,
]
```

### 2.2 Line Length

PEP 8 canonical: 79 chars (code), 72 chars (docstrings/comments).

| Mode | Code | Docs | When |
|------|------|------|------|
| Strict PEP 8 | 79 | 72 | Open-source libraries |
| Team extended | 99 | 72 | Internal projects |
| Modern (Ruff default) | 88 | 79 | New greenfield projects |

Document the choice in pyproject.toml. Choose one, never mix.

Wrapping methods (in order of preference):

```python
# 1. Implicit continuation in parentheses (best)
result = some_very_long_function_name(
    argument_one,
    argument_two,
    keyword=value,
)

# 2. Wrap expression in parentheses
long_string = (
    "This is a very long string that "
    "spans multiple lines."
)

# 3. Backslash — only when parentheses are impossible
# Python < 3.10 multi-context managers:
with open('/path/to/file_one') as file_1, \
     open('/path/to/file_2', 'w') as file_2:
    file_2.write(file_1.read())

# Python 3.10+ — parenthesised with (preferred)
with (
    open('/path/to/file_one') as file_1,
    open('/path/to/file_2', 'w') as file_2,
):
    file_2.write(file_1.read())
```

### 2.3 Binary Operator Line Breaks

Break BEFORE binary operators (Knuth style — PEP 8 revised 2013):

```python
# Correct — operator leads the line
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)

# Wrong — operator trails (old style)
income = (gross_wages +
          taxable_interest +
          (dividends - qualified_dividends) -
          ira_deduction)
```

### 2.4 Blank Lines

| Context | Blank lines |
|---------|-------------|
| Between top-level functions/classes | 2 |
| Between methods in a class | 1 |
| Between related function groups | 1 (sparingly) |
| Inside function for logical sections | 1 (sparingly) |

```python
class MyClass:
    """Class docstring."""

    CLASS_CONSTANT = 42

    def __init__(self) -> None:
        self.value = 0

    def method_one(self) -> int:
        return self.value

    def method_two(self) -> str:
        return str(self.value)


class AnotherClass:
    pass
```

### 2.5 Source File Encoding

Always UTF-8. Never add encoding declaration in Python 3 — it is redundant.

```python
# WRONG in Python 3
# -*- coding: utf-8 -*-
```

---

## 3. IMPORTS

### 3.1 Grouping and Ordering

Four groups, blank line between each, in this exact order:

```python
"""Module docstring."""

from __future__ import annotations  # Must be first if used

__all__ = ["PublicClass", "public_function"]
__version__ = "1.0.0"

# Group 1: Standard library
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Group 2: Third-party
import httpx
import structlog
from pydantic import BaseModel, Field

# Group 3: Local application
from myapp.core.config import settings
from myapp.core.exceptions import NotFoundError
from myapp.models.user import User

# Group 4: Type-checking only (no circular import at runtime)
if TYPE_CHECKING:
    from myapp.services.auth import AuthService
    from myapp.repositories.user_repository import UserRepository
```

### 3.2 Import Style Rules

```python
# Correct — one module per line
import os
import sys

# Correct — multiple names from one module
from subprocess import PIPE, Popen
from typing import Any, Optional, Union

# WRONG — multiple modules on one line
import sys, os

# WRONG — star import
from os.path import *

# Exception: star imports in __init__.py ONLY for public API re-export
# when __all__ is explicitly declared in the source module.
```

### 3.3 Absolute vs Relative

```python
# Preferred — absolute imports
from mypackage.utils import helper
from mypackage.models.user import User

# Acceptable — explicit relative imports within a package
from . import sibling_module
from .sibling_module import SomeClass
from ..parent_module import ParentClass
```

### 3.4 Conditional and Deferred Imports

```python
# Optional dependency
try:
    import ujson as json
except ImportError:
    import json

# Platform-specific
import sys
if sys.platform == "win32":
    import winreg

# Expensive optional (deferred)
def get_numpy_array(data: list) -> "np.ndarray":
    """Convert data to numpy array. Requires numpy."""
    import numpy as np  # Deferred: optional heavy dependency
    return np.array(data)
```

---

## 4. MODULE-LEVEL DUNDERS

After module docstring, before regular imports. `from __future__` comes before dunders.

```python
"""Module docstring."""

from __future__ import annotations

__all__ = ["UserManager", "create_user"]
__version__ = "2.1.0"
__author__ = "AurigaIT Engineering"

import os
from typing import Any
```

---

## 5. STRING QUOTES

PEP 8 has no preference. Projects must pick one and be consistent.
Ruff/Black default: double quotes.

```python
name = "Jane Doe"                    # Project default (double)
greeting = 'He said "hello"'         # Use other to avoid backslash
path = "It's a beautiful day"        # Use other to avoid backslash

# Triple-quoted — ALWAYS double (PEP 257 requirement)
docstring = """This is a docstring."""

# f-strings follow project default
full_name = f"Hello, {first_name} {last_name}!"

# Python 3.12+: nested quotes can match outer quotes
message = f"User: {'admin' if is_admin else 'guest'}"  # py3.12+ only
```

---

## 6. WHITESPACE RULES

### 6.1 Pet Peeves (Never Do These)

```python
# WRONG — space inside delimiters
spam( ham[ 1 ], { eggs: 2 } )
# Correct
spam(ham[1], {eggs: 2})

# WRONG — space before comma
bar = (0, )
# Correct
foo = (0,)

# WRONG — inconsistent slice spacing
ham[lower + offset:upper + offset]
ham[1: 9], ham[1 :9]
# Correct — colon acts as binary operator in slices
ham[lower:upper]
ham[lower+offset : upper+offset]
ham[lower + offset : upper + offset]

# WRONG — space before function call
spam (1)
# Correct
spam(1)

# WRONG — space before subscript
dct ['key'] = lst [index]
# Correct
dct['key'] = lst[index]
```

### 6.2 Operator Spacing

```python
# WRONG — aligning with spaces
x             = 1
long_variable = 3

# Correct
x = 1
long_variable = 3

# Correct — tighter spacing shows precedence
x = x*2 - 1
hypot2 = x*x + y*y
c = (a+b) * (a-b)

# Correct — spaces around annotation arrow
def munge(input: AnyStr) -> None: ...

# WRONG — no spaces around arrow
def munge()->PosInt: ...

# Correct — NO space around = for unannotated keyword args
def complex(real, imag=0.0):
    return magic(r=real, i=imag)

# Correct — SPACE around = when BOTH annotation AND default present
def munge(sep: AnyStr = None): ...
def munge(input: AnyStr, sep: AnyStr = None, limit=1000): ...

# WRONG — no space when annotation + default present
def munge(input: AnyStr=None): ...
```

### 6.3 Compound Statements

```python
# Correct
if foo == "blah":
    do_blah_thing()

# WRONG
if foo == "blah": do_blah_thing()
do_one(); do_two(); do_three()

# DEFINITELY WRONG
if foo == "blah": do_blah_thing()
else: do_non_blah_thing()

try: something()
finally: cleanup()
```

### 6.4 Variable Annotations (PEP 526)

```python
# Correct
code: int
name: str = "default"

class Point:
    coords: tuple[int, int]
    label: str = "<unknown>"

# WRONG
code:int           # No space after colon
code : int         # Space before colon
result: int=0      # No spaces around = when annotation present
```

---

## 7. TRAILING COMMAS

```python
# MANDATORY — single-element tuple
FILES = ("setup.cfg",)

# WRONG — this is just a string in parentheses, not a tuple
FILES = ("setup.cfg")

# RECOMMENDED — trailing comma on expandable structures
# Produces 1-line diffs; clean git blame; essential for large-team review
FILES = [
    "setup.cfg",
    "tox.ini",
    "pyproject.toml",   # Add new item = 1 line diff, not 2
]

initialize(
    FILES,
    error=True,
)

# WRONG — trailing comma on same line as closing delimiter
FILES = ["setup.cfg", "tox.ini",]
```

Why this matters at scale: Without trailing commas, adding one item to a 20-item list
diffs as 2 lines (comma on prev item + new item). With trailing commas, it's 1 line.
Across hundreds of PRs per day in a large team, this dramatically reduces review noise
and false blame in git blame.

---

## 8. COMMENTS

### 8.1 Core Rules

- Comments that contradict code are WORSE than no comments. Keep them updated.
- Write as complete sentences. Capitalize first word unless it is an identifier.
- Write in English (global audience).
- Explain WHY, not WHAT. Code shows what; comments show intent.

```python
# USEFUL — explains why
x = x + 1  # Compensate for border pixel (designer req, issue #443)

# USELESS — states the obvious
x = x + 1  # Increment x
```

### 8.2 Block Comments

```python
def process_payment(order: Order, card: CreditCard) -> Receipt:
    # Validate card locally before contacting the gateway.
    # Local validation reduces latency and gateway fees.
    # A failed local validation never touches the network.
    if not _validate_card_format(card):
        raise PaymentError("Invalid card format", code="INVALID_CARD")

    # Attempt charge with exponential backoff on transient failures.
    # Gateway returns HTTP 503 during peak hours (observed production pattern).
    for attempt in range(MAX_PAYMENT_RETRIES):
        try:
            return _charge_card(order, card)
        except GatewayTransientError:
            if attempt == MAX_PAYMENT_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
```

### 8.3 Inline Comments

Separated by at least 2 spaces. Start with `# `.

```python
# Justified — magic constant needs context
MAX_REDIRECTS = 10  # RFC 7231 §6.4 recommends ≤5; allow more for internal proxies

# Unjustified — noise
counter = 0  # Set counter to zero
```

### 8.4 TODO / FIXME Convention (Team Standard)

```python
# TODO(username): Description. Ticket link.
# FIXME(username): Something broken, immediate attention needed.
# HACK(username): Workaround for external issue. Link to ticket.
# NOTE(username): Important context for future maintainers.

# Examples:
# TODO(arpit): Remove after Django 5.x upgrade. JIRA-1234
# HACK(nishant): Gateway returns 200 on auth failure; check body instead. GW-1234
# FIXME(rishap): Race condition in concurrent writes. ENG-5678
```

---

## 9. DOCSTRINGS (PEP 257)

### 9.1 What Must Have Docstrings

| Construct | Required |
|-----------|----------|
| Public module | Yes — purpose and exports |
| Public class | Yes — what it represents and how to use it |
| `__init__` | Yes if args need explanation |
| Public method/function | Yes — all |
| Non-public method | Yes if complex; short comment acceptable for trivial |
| Abstract method | Yes — always (documents the contract subclasses fulfill) |
| Property | Yes if purpose not obvious from name |

### 9.2 One-Line Docstrings

```python
def square(x: float) -> float:
    """Return the square of x."""  # Closing """ on same line
```

Imperative mood — "Do X" not "Does X":

```python
# Correct — imperative
def fetch_user(user_id: int) -> User:
    """Fetch a user by ID from the database."""

# WRONG — descriptive
def fetch_user(user_id: int) -> User:
    """Fetches a user by ID."""
```

### 9.3 Multi-Line Docstrings (Google Style — Team Standard)

```python
def create_order(
    customer_id: int,
    items: list[OrderItem],
    *,
    discount_code: str | None = None,
    currency: str = "INR",
) -> Order:
    """Create and persist a new customer order.

    Validates items, applies any discount, calculates tax,
    and writes the order to the database. Raises on any
    validation failure before touching the database.

    Args:
        customer_id: Database ID of the ordering customer.
            Must reference an active customer record.
        items: Non-empty list of items. Each must have
            positive quantity and valid product_id.
        discount_code: Optional promotional code. Invalid codes
            silently ignored. Defaults to None.
        currency: ISO 4217 currency code. Defaults to "INR".
            Must be in SUPPORTED_CURRENCIES.

    Returns:
        Persisted Order instance with id, created_at, total.

    Raises:
        ValueError: If items is empty.
        CustomerNotFoundError: If customer_id is not active.
        ProductNotFoundError: If any item's product_id is invalid.
        CurrencyError: If currency not in SUPPORTED_CURRENCIES.

    Example:
        >>> item = OrderItem(product_id=1, quantity=2)
        >>> order = create_order(customer_id=42, items=[item])
        >>> order.status
        'pending'

    Note:
        NOT idempotent. Calling twice creates two separate orders.
    """
```

### 9.4 Class Docstrings

```python
class PaymentGateway:
    """Client for the external payment gateway REST API.

    Wraps the gateway with retry logic, circuit breaking,
    and structured error mapping. All monetary values in
    smallest currency unit (e.g., paise for INR).

    Attributes:
        timeout_seconds: Request timeout. Defaults to 10.
        max_retries: Retries on transient errors. Defaults to 3.

    Example:
        >>> gateway = PaymentGateway()
        >>> receipt = gateway.charge(amount_paise=10000, card=card)
    """

    def __init__(self, timeout_seconds: int = 10, max_retries: int = 3) -> None:
        """Initialise the payment gateway client.

        Args:
            timeout_seconds: HTTP timeout per request.
            max_retries: Retry attempts on HTTP 503/connection errors.
                Exponential backoff. Set 0 to disable retries.
        """
```

### 9.5 Module Docstrings

```python
"""User management service.

Provides CRUD operations for user accounts including creation,
authentication, profile updates, and deactivation.

Typical usage::

    from myapp.services import user_service

    user = user_service.create(email="user@example.com", name="Jane")
    token = user_service.authenticate(email="user@example.com", password="...")

Public API:
    create_user: Create a new user account.
    authenticate_user: Validate credentials and return a JWT.
    deactivate_user: Soft-delete a user account.
"""
```

---

## 10. NAMING CONVENTIONS

### 10.1 Complete Reference

| Construct | Style | Example | Notes |
|-----------|-------|---------|-------|
| Package | `lowercase` | `mypackage` | No underscores preferred |
| Module | `lower_with_underscores` | `user_service.py` | Short, descriptive |
| Class | `CapWords` | `UserService` | Acronyms ALL CAPS: `HTTPClient` |
| Exception | `CapWords` + `Error` | `UserNotFoundError` | Or Warning if not an error |
| Type variable | `CapWords`, short | `T`, `KT_contra` | `_co`/`_contra` for variance |
| Function | `lower_with_underscores` | `get_active_users` | Verb-noun |
| Method (instance) | `lower_with_underscores` | `calculate_total` | First arg: self |
| Method (class) | `lower_with_underscores` | `from_dict` | First arg: cls |
| Method (static) | `lower_with_underscores` | `validate_email` | No implicit arg |
| Module constant | `UPPER_CASE` | `MAX_RETRIES = 3` | |
| Instance variable | `lower_with_underscores` | `self.user_id` | |
| Private method/var | `_name` | `_validate_token` | Single underscore |
| Name-mangled | `__name` | `self.__secret` | Use sparingly |
| Dunder | `__name__` | `__init__`, `__all__` | Never invent new ones |
| TypeAlias (3.10+) | `CapWords` | `UserId: TypeAlias = int` | |
| type stmt (3.12+) | `CapWords` | `type UserId = int` | |

### 10.2 Names to Absolutely Avoid

```python
# Never as single-char variable names:
l   # Indistinguishable from 1 in many fonts
O   # Indistinguishable from 0
I   # Indistinguishable from 1 or l

# Never shadow built-ins:
list = []       # Destroys built-in list for this scope
dict = {}
type = "user"   # Shadows built-in type — extremely common mistake
id = 42         # Shadows built-in id
input = ...
filter = ...
map = ...
next = ...
min = ...
max = ...

# Keyword clash — trailing underscore is correct resolution:
class_ = MyClass    # Better than clss
type_ = "user"      # Better than typ
lambda_ = 0.01      # Better than lam
```

### 10.3 Naming Deep Guidelines

Functions — verb-first, describe what they do:

```python
# Correct
def get_user(user_id: int) -> User: ...
def create_order(customer_id: int) -> Order: ...
def validate_email(email: str) -> bool: ...
def send_welcome_email(user: User) -> None: ...

# Boolean functions — is_/has_/can_/should_ prefix
def is_active(user: User) -> bool: ...
def has_permission(user: User, action: str) -> bool: ...
def can_refund(order: Order) -> bool: ...

# WRONG — ambiguous (get? create? delete?)
def user(user_id: int) -> User: ...
def email(user: User) -> None: ...
```

Classes — noun or noun phrase:

```python
class UserService: ...
class PaymentGateway: ...
class OrderRepository: ...

# Mixin classes — Mixin suffix
class TimestampMixin: ...
class SoftDeleteMixin: ...

# Abstract/base classes
class AbstractRepository: ...
class BaseView: ...

# WRONG — vague
class Manager: ...   # Manager of what?
class Helper: ...
class Utils: ...     # Use a module, not a class
```

Constants — named, never magic numbers:

```python
# Correct
MAX_LOGIN_ATTEMPTS = 5       # Locks account after N failures (security policy)
DEFAULT_PAGE_SIZE = 20       # Matches DB index scan page size
TOKEN_EXPIRY_SECONDS = 900   # 15 minutes — PCI DSS session requirement

# WRONG
if attempts > 5:             # Where does 5 come from?
    lock_account()

# Domain state constants — always Enum
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

# WRONG — string constants scattered across files
status = "pending"   # No validation, no autocomplete, typo-prone
```

### 10.4 Public and Internal Interfaces

```python
# Public — documented, stable contract
class UserService:
    def create_user(self, email: str, name: str) -> User: ...
    def get_user(self, user_id: int) -> User: ...

# Internal — single underscore, may change
class UserService:
    def _validate_email_uniqueness(self, email: str) -> None: ...
    def _hash_password(self, plain: str) -> str: ...

# Name-mangled — prevents accidental override in subclasses
class Authenticator:
    def __init__(self) -> None:
        self.__secret_key: str = settings.secret_key
```

Declare `__all__` in every module forming a public API:

```python
# myapp/services/__init__.py
__all__ = [
    "UserService",
    "OrderService",
    "PaymentService",
]
```

---

## 11. TYPE ANNOTATIONS

### 11.1 Version Compatibility Matrix

| Feature | PEP | Min Python | Notes |
|---------|-----|------------|-------|
| Basic type hints | 484 | 3.5 | `def f(x: int) -> str` |
| `Optional[X]` | 484 | 3.5 | Use `X \| None` in 3.10+ |
| `Union[X, Y]` | 484 | 3.5 | Use `X \| Y` in 3.10+ |
| `from __future__ import annotations` | 563 | 3.7 | Defers evaluation; forward refs |
| Built-in generics `list[int]` | 585 | 3.9 | Before 3.9: use `List[int]` |
| `X \| Y` union syntax | 604 | 3.10 | Before 3.10: use `Union[X, Y]` |
| Variable annotations | 526 | 3.6 | `x: int = 5` |
| `ParamSpec`, `Concatenate` | 612 | 3.10 | Higher-order function typing |
| `TypeAlias` (explicit) | 613 | 3.10 | `UserId: TypeAlias = int` |
| `Self` type | 673 | 3.11 | Self-referential return types |
| `TypeVarTuple`, `Unpack` | 646 | 3.11 | Variadic generics |
| `type` statement | 695 | 3.12 | `type UserId = int` |
| `@override` decorator | 698 | 3.12 | Explicit override marking |
| `except*` (ExceptionGroup) | 654 | 3.11 | New exception handling pattern |

### 11.2 Version-Specific Strategies

Strategy A — from __future__ import annotations (Python 3.7+, RECOMMENDED):

```python
from __future__ import annotations


def get_user(user_id: int) -> User | None:   # | OK with __future__ on 3.7+
    ...

class UserService:
    users: list[User]           # Built-in generic OK with __future__
    cache: dict[str, User]
```

Strategy B — typing imports for Python 3.6 and below (legacy projects ONLY):

```python
from typing import Dict, List, Optional, Tuple, Union

def get_user(user_id: int) -> Optional[User]: ...
def batch_get(ids: List[int]) -> Dict[int, User]: ...
def merge(a: User, b: User) -> Union[User, None]: ...
```

Strategy C — version-conditional for libraries supporting wide ranges:

```python
from __future__ import annotations
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self  # pip install typing_extensions

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

UserId: TypeAlias = int
```

### 11.3 Key Annotation Patterns

```python
from __future__ import annotations
from collections.abc import Callable, Generator, Iterator, Sequence
from typing import Any, ClassVar, Final, Literal, TypeVar, overload

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

# ClassVar — class-level, not per-instance
class MyClass:
    instances: ClassVar[list[MyClass]] = []
    MAX_SIZE: ClassVar[int] = 100

# Final — must not be reassigned
MAX_SIZE: Final = 100
USER_ROLES: Final[frozenset[str]] = frozenset({"admin", "editor", "viewer"})

# Literal — exact value constraints
def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None: ...

# overload — multiple call signatures
@overload
def process(value: int) -> str: ...
@overload
def process(value: str) -> int: ...
def process(value: int | str) -> str | int:
    if isinstance(value, int):
        return str(value)
    return int(value)

# Protocol — structural subtyping (duck typing with type safety)
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()

# Generator
def count_up(n: int) -> Generator[int, None, None]:
    for i in range(n):
        yield i
```

### 11.4 When Any Is Acceptable

```python
# Acceptable — document why
def deserialize(data: Any) -> dict[str, Any]:
    # Any: external JSON, shape unknown until runtime.
    return json.loads(data)

# Acceptable — third-party without stubs
import legacy_lib  # type: ignore[import]  # No stubs for legacy_lib

# NOT acceptable — laziness
def process(x: Any) -> Any:  # Defeats type checking
    ...
```

---

## 12. PROGRAMMING RECOMMENDATIONS

### 12.1 Singleton Comparisons

```python
# Correct
if foo is None: ...
if foo is not None: ...

# WRONG — equality for None (can be fooled by __eq__)
if foo == None: ...

# TRAP — not equivalent:
if foo is not None:  # True even when foo is 0, "", [], False
if foo:              # False when foo is 0, "", [], False, or None
```

### 12.2 Boolean Comparisons

```python
# Correct — truthiness
if greeting: ...
if not items: ...

# WRONG — explicit comparison to True/False
if greeting == True: ...
if greeting is True: ...  # Worse

# Correct — empty sequence check
if not seq: ...

# WRONG — len check
if len(seq) == 0: ...
if not len(seq): ...
```

### 12.3 Return Statement Consistency

```python
# Correct — all returns explicit
def find_user(user_id: int) -> User | None:
    if user_id <= 0:
        return None
    user = db.get(user_id)
    if user is None:
        return None
    return user

# WRONG — inconsistent (implicit return None at end)
def find_user(user_id: int) -> User | None:
    if user_id <= 0:
        return None
    user = db.get(user_id)
    if user:
        return user
    # Implicit return None — mypy catches this, humans miss it
```

### 12.4 Exception Handling — Complete Reference

```python
# Correct — specific exception, minimum code in try, else for success path
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)  # else: runs only if no exception was raised

# WRONG — too much in try clause (handle_value can also raise KeyError)
try:
    return handle_value(collection[key])
except KeyError:
    return key_not_found(key)

# WRONG — bare except catches SystemExit, KeyboardInterrupt
try:
    risky()
except:
    pass

# Acceptable bare except ONLY when logging + re-raising
try:
    risky()
except Exception:
    logger.exception("risky failed")
    raise

# Exception chaining — preserve original context
try:
    result = gateway.charge(card)
except requests.Timeout as exc:
    raise PaymentTimeoutError("Gateway timed out") from exc

# Suppress context intentionally
try:
    return cache[key]
except KeyError:
    raise CacheMissError(key) from None  # from None hides __context__

# Python 3.3+ OS errors — use exception hierarchy, not errno
try:
    os.remove(path)
except FileNotFoundError:   # Specific, readable, no errno import needed
    pass
except PermissionError:
    raise

# OLD — fragile errno pattern (avoid in Python 3)
import errno
try:
    os.remove(path)
except OSError as exc:
    if exc.errno == errno.ENOENT:  # Fragile
        pass
```

### 12.5 Context Managers

```python
# Correct
with open("/path/to/file") as f:
    data = f.read()

# Correct — explicit about what the context manager does
with conn.begin_transaction():
    do_stuff_in_transaction(conn)

# WRONG — ambiguous
with conn:
    do_stuff_in_transaction(conn)

# Correct — multiple CMs
with open("input.txt") as infile, open("output.txt", "w") as outfile:
    outfile.write(infile.read())

# Correct — parenthesised form (Python 3.10+)
with (
    open("input.txt") as infile,
    open("output.txt", "w") as outfile,
    lock,
):
    outfile.write(infile.read())
```

### 12.6 String Operations

```python
# Correct
if filename.startswith("tmp_"): ...
if filename.endswith((".png", ".jpg", ".webp")): ...  # accepts tuple

# WRONG — fragile slicing
if filename[:4] == "tmp_": ...

# Correct — isinstance
if isinstance(obj, int): ...

# WRONG — type comparison (breaks with subclasses)
if type(obj) == int: ...

# Correct — join for concatenation (O(n))
result = "".join(str(item) for item in items)

# WRONG — += in loop (O(n²) in theory, fragile across implementations)
result = ""
for item in items:
    result += str(item)
```

### 12.7 Lambda vs def

```python
# Correct — def for named functions (traceback shows name)
def double(x: int) -> int:
    return x * 2

# WRONG — lambda assigned to name (traceback shows <lambda>)
double = lambda x: x * 2

# Acceptable lambda — as inline argument
sorted_users = sorted(users, key=lambda u: (u.last_name, u.first_name))

# Better when key is complex — named function
def user_sort_key(user: User) -> tuple[str, str]:
    return (user.last_name, user.first_name)

sorted_users = sorted(users, key=user_sort_key)
```

### 12.8 Rich Comparisons

```python
from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, major: int, minor: int) -> None:
        self.major = major
        self.minor = minor

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)

# total_ordering generates __le__, __gt__, __ge__ automatically
```

### 12.9 Never Flow Control in Finally

```python
# WRONG — return in finally silently swallows active exception
def dangerous() -> int:
    try:
        1 / 0            # Raises ZeroDivisionError
    finally:
        return 42        # ZeroDivisionError silently swallowed. Caller never knows.

# Correct — finally for cleanup only
def safe_operation() -> None:
    connection = None
    try:
        connection = db.connect()
        connection.execute(query)
    except DatabaseError:
        logger.exception("Query failed")
        raise
    finally:
        if connection is not None:
            connection.close()
```

### 12.10 Mutable Default Arguments

```python
# WRONG — the default list is SHARED across all calls
def append_item(item: str, target: list[str] = []) -> list[str]:
    target.append(item)
    return target

append_item("a")  # Returns ["a"]
append_item("b")  # Returns ["a", "b"] — NOT ["b"]!

# Correct — sentinel pattern
def append_item(
    item: str,
    target: list[str] | None = None,
) -> list[str]:
    if target is None:
        target = []
    target.append(item)
    return target

# Correct — dataclass field factory
from dataclasses import dataclass, field

@dataclass
class Config:
    allowed_hosts: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
```

---

## 12.11 Late Binding Closures

Python closures bind variables **by reference at call time**, not at definition time.
This is a common source of bugs when generating functions in loops:

```python
# WRONG — all five functions capture the same i, which is 4 after loop ends
def make_multipliers_bad():
    return [lambda x: i * x for i in range(5)]

for fn in make_multipliers_bad():
    print(fn(2))   # prints: 8 8 8 8 8  ← all use i=4


# CORRECT — capture current value with a default argument
def make_multipliers():
    return [lambda x, i=i: i * x for i in range(5)]

for fn in make_multipliers():
    print(fn(2))   # prints: 0 2 4 6 8  ✅


# ALSO CORRECT — use functools.partial for cleaner intent
from functools import partial
from operator import mul

def make_multipliers():
    return [partial(mul, i) for i in range(5)]
```

**Rule:** When creating callables inside a loop that reference the loop variable,
always capture the current value via a default argument `i=i` or `functools.partial`.
This is not specific to `lambda` — regular `def` inside a loop has identical behaviour.

---

## 12.12 Python Idioms Reference

### Unpacking & Destructuring

```python
# Basic tuple/list unpacking
filename, ext = "photo.orig.png".rsplit(".", 1)

# Swap without temp variable
a, b = b, a

# Extended unpacking (Python 3.0+)
first, *rest = [1, 2, 3, 4]         # first=1, rest=[2,3,4]
first, *middle, last = [1, 2, 3, 4] # first=1, middle=[2,3], last=4

# Ignore unwanted values — use __ (double underscore)
# Single _ risks colliding with gettext alias or REPL last-result
basename, __, ext = "archive.tar.gz".rpartition(".")
```

### List / Collection Construction

```python
# WRONG — [[]]*4 creates 4 references to the SAME list
four_lists = [[]] * 4
four_lists[0].append("x")
print(four_lists)  # [['x'], ['x'], ['x'], ['x']] ← bug!

# CORRECT — list comprehension creates 4 independent lists
four_lists = [[] for __ in range(4)]
four_lists[0].append("x")
print(four_lists)  # [['x'], [], [], []] ✅

# CORRECT — immutable repetition is fine (None, int, str are not mutated)
four_nones = [None] * 4   # safe; None is immutable
```

### String Building

```python
parts = ["s", "p", "a", "m"]

# WRONG — repeated += creates a new string object each iteration O(n²)
result = ""
for c in parts:
    result += c

# CORRECT — accumulate in list, join once O(n)
result = "".join(parts)

# ALSO CORRECT — when concatenating a known small number of strings
# direct addition is readable and fast
full_name = first_name + " " + last_name
```

### Membership Testing: list vs set

```python
# list membership: O(n) — scans every element
items_list = ["foo", "bar", "baz", "qux"]
if "baz" in items_list:   # fine for small lists
    ...

# set membership: O(1) — hash lookup; use for repeated checks or large collections
items_set = {"foo", "bar", "baz", "qux"}
if "baz" in items_set:    # always prefer for repeated or large-collection membership
    ...

# Convert once, check many times
VALID_STATUSES = frozenset({"pending", "processing", "shipped", "delivered"})

def is_valid_status(status: str) -> bool:
    return status in VALID_STATUSES  # O(1) always
```

### Dictionary Access

```python
d = {"host": "localhost", "port": 5432}

# WRONG — KeyError if key absent
value = d["timeout"]

# CORRECT — provide a default
timeout = d.get("timeout", 30)

# CORRECT — membership check before access
if "timeout" in d:
    timeout = d["timeout"]
```

### Enumerate over Range+Index

```python
items = ["alpha", "beta", "gamma"]

# WRONG — manual index
for i in range(len(items)):
    print(f"{i}: {items[i]}")

# CORRECT — enumerate is clearer and works on any iterable
for i, item in enumerate(items):
    print(f"{i}: {item}")

# With non-zero start
for i, item in enumerate(items, start=1):
    print(f"{i}: {item}")
```

---

## 12.13 Function Arguments — Design Rules

```python
# ✅ Positional: few args, natural order, obvious meaning
def send(message: str, recipient: str) -> None: ...
def point(x: float, y: float) -> Point: ...

# ✅ Keyword with defaults: more than 2-3 params, optional behaviour
def send(message: str, to: str, cc: str | None = None, bcc: str | None = None) -> None: ...

# ✅ *args: homogeneous variadic positional — but consider explicit list param instead
def log_events(*events: Event) -> None: ...
# Explicit alternative (often clearer):
def log_events(events: list[Event]) -> None: ...

# ✅ **kwargs: genuinely dynamic keyword passing (logging formatters, middleware)
def log(message: str, **context: object) -> None: ...

# ❌ *args/**kwargs as escape hatch for unclear signature — never do this
def process(*args, **kwargs): ...   # What does this actually take?
```

**Rules:**
- A function's first and last lines should tell another developer what it does.
- Never add an optional argument "just in case" — it's much harder to remove than to add.
- Use `None` as the sentinel for "not provided", never a mutable default.
- Rename `*args` / `**kwargs` when clearer names exist: `*events`, `**context`.

---

## 12.14 Pure Functions & Minimising Side Effects

**Pure functions** always produce the same output for the same input and have no side effects.
They are easier to test, refactor, and reason about.

```python
# IMPURE — depends on external state; untestable without mocking
def get_discount_price(product_id: int) -> Decimal:
    product = db.query(Product).get(product_id)   # side effect: DB call
    if datetime.now().weekday() == 5:              # external state: system time
        return product.price * Decimal("0.9")
    return product.price

# PURE — same input always gives same output; no external dependencies
def calculate_discount_price(price: Decimal, is_weekend: bool) -> Decimal:
    """Return discounted price if weekend, else full price."""
    if is_weekend:
        return price * Decimal("0.9")
    return price

# Call site: inject the dependencies
product = db.query(Product).get(product_id)
is_weekend = datetime.now().weekday() == 5
final_price = calculate_discount_price(product.price, is_weekend)
```

**Rules:**
- Business logic functions should be pure: inject their inputs, return their outputs.
- Side effects (DB writes, HTTP calls, file I/O) belong in the outermost layer (services, repositories).
- Avoid functions that modify objects they didn't create (hidden coupling).
- Avoid module-level mutable state — it creates race conditions in multi-process web apps.

---

## 12.15 Variable Naming Under Dynamic Typing

Reassigning a variable to a different type within the same scope destroys readability.
Type checkers (mypy, pyright) will catch this, but the convention must be proactive:

```python
# WRONG — items is a string, then a list, then a set
items = "a b c d"
items = items.split()
items = set(items)

# CORRECT — distinct names signal distinct types to every reader
items_str = "a b c d"
items_list = items_str.split()
items_set = set(items_list)

# WRONG — reusing 'a' for completely different things
a = 1
a = "the answer is {}".format(a)

# CORRECT — short helper function captures the transformation
def format_answer(n: int) -> str:
    return f"the answer is {n}"

answer = format_answer(1)
```

**Rules:**
- Never reuse a variable name for a different conceptual type within the same function.
- When a value must be transformed through multiple types, give each stage a name.
- Rely on type annotations + mypy to enforce this automatically.

---

## 13. ANTI-PATTERNS — PRODUCTION INCIDENT REFERENCE

Each pattern below has caused a real production incident.

### 13.1 Silent Exception Swallowing

```python
# WORST pattern — payment may or may not have succeeded, no one knows
try:
    process_payment(order)
except Exception:
    pass

# Minimum acceptable
try:
    process_payment(order)
except Exception:
    logger.exception("Payment failed", order_id=order.id)
    raise
```

### 13.2 Overly Broad Exception Catching

```python
# WRONG — masks AttributeError, NameError, all programming errors
def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}

# Correct
def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc
```

### 13.3 Global State

```python
# WRONG — hidden coupling, thread-unsafe, untestable
_current_user = None

def set_current_user(user: User) -> None:
    global _current_user
    _current_user = user

# Correct — explicit dependency injection
def process_request(request: Request, current_user: User) -> Response: ...

# Correct — contextvars for async (Python 3.7+)
from contextvars import ContextVar
current_user: ContextVar[User | None] = ContextVar("current_user", default=None)
```

### 13.4 type() Instead of isinstance()

```python
# WRONG — fails for subclasses, ABCs
if type(value) == list: ...

# Correct
if isinstance(value, list): ...

# Correct — with ABCs (accepts list, tuple, str, UserList...)
from collections.abc import Sequence
if isinstance(value, Sequence): ...
```

### 13.5 String Formatting

```python
# WRONG — % style
msg = "Hello, %s! You have %d messages." % (name, count)

# WRONG — .format()
msg = "Hello, {}! You have {} messages.".format(name, count)

# Correct — f-strings (Python 3.6+)
msg = f"Hello, {name}! You have {count} messages."
debug = f"Value: {value:.2f}"
padded = f"ID: {user_id:05d}"

# Correct — join for loops
result = "".join(str(item) for item in items)
```

**F-string expression constraints** (Django coding style — applies to all projects):

```python
# ✅ ALLOWED — plain variable access
f"Hello {user}"
f"Hello {user.name}"
f"Hello {self.user.name}"

# ❌ DISALLOWED — function calls inside braces
f"Hello {get_user()}"
f"Age: {user.age * 365.25} days"

# ✅ CORRECT — extract to a local variable first
user = get_user()
f"Hello {user}"

user_days_old = user.age * 365.25
f"Age: {user_days_old} days"
```

**F-strings and translation:** Never use f-strings for strings that may require
translation (error messages, UI labels, log messages shown to users).
Use `%`-style formatting with `gettext` instead:

```python
# WRONG — f-strings are not translatable
from django.utils.translation import gettext as _
raise ValidationError(f"User {username} not found")   # ❌

# CORRECT
raise ValidationError(_("User %(username)s not found") % {"username": username})  # ✅
```

---

### 13.6 Suppression Comments (NOQA / type: ignore)

**Always specify the exact error code. Bare suppression is prohibited.**

```python
# WRONG — bare suppression masks unknown future errors
import unused_module  # NOQA
x: int = "not an int"  # type: ignore

# CORRECT — targeted suppression with explanation
import unused_module  # NOQA: F401  # Re-exported as part of public API
x: int = "not an int"  # type: ignore[assignment]  # Legacy interface contract

# WRONG — pylint bare disable
def func(foo, bar):  # pylint: disable=unused-argument
    ...

# CORRECT — specific code + comment above if explanation doesn't fit inline
# PYLINT NOTE: bar is required by the interface contract but unused in this impl.
def func(foo, bar):  # pylint: disable=unused-argument
    ...
```

**Rules:**
- Ruff/flake8: always `# NOQA: E501` not `# NOQA`.
- mypy: always `# type: ignore[specific-error]` not `# type: ignore`.
- pylint: always `# pylint: disable=specific-rule` not a blanket disable.
- If the explanation doesn't fit on the same line, add a comment above prefixed with the tool name: `# MYPY NOTE:`, `# PYLINT NOTE:`, `# RUFF NOTE:`.
- Suppressions require code review approval — treat them as technical debt.

---

## 14. VERSION COMPATIBILITY MATRIX

| Feature | 3.6 | 3.7 | 3.8 | 3.9 | 3.10 | 3.11 | 3.12 | 3.13 |
|---------|-----|-----|-----|-----|------|------|------|------|
| f-strings | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `from __future__ import annotations` | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| walrus `:=` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `list[int]` (not `List[int]`) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `X \| Y` union | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `match` statement | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Parenthesized `with` | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `Self` type | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `TypeAlias` explicit | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `except*` ExceptionGroup | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `type X = Y` statement | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `@override` decorator | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| f-string nested quotes | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Free-threaded (GIL optional) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

Minimum for new projects: Python 3.10.
Django 4.2+, FastAPI 0.100+, SQLAlchemy 2.x require Python 3.10+.

---

## 15. TOOLCHAIN CONFIGURATION

### 15.1 Complete pyproject.toml

```toml
[tool.ruff]
target-version = "py310"
line-length = 88
indent-width = 4

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "S",      # flake8-bandit (security)
    "B",      # flake8-bugbear
    "A",      # flake8-builtins (shadowing)
    "C4",     # flake8-comprehensions
    "T20",    # flake8-print
    "RET",    # flake8-return
    "SIM",    # flake8-simplify
    "ERA",    # eradicate (commented-out code)
    "PL",     # Pylint
    "RUF",    # Ruff-specific rules
]
ignore = [
    "S101",    # Allow assert in tests
    "B008",    # Allow function calls in defaults (FastAPI Depends)
    "RUF012",  # Mutable class attrs — dataclass/pydantic handled
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S106", "PLR2004"]
"migrations/**/*.py" = ["N999", "E501"]

[tool.ruff.lint.isort]
known-first-party = ["myapp"]
force-sort-within-sections = true

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
disallow_untyped_decorators = true
show_error_codes = true
pretty = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = ["celery.*", "kombu.*"]
ignore_missing_imports = true
```

### 15.2 pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-redis]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
      - id: check-added-large-files
        args: ["--maxkb=500"]
```

---

## APPENDIX: VIOLATIONS QUICK REFERENCE

CRITICAL — block merge immediately:
- Bare `except:` without log + re-raise
- `except Exception: pass` — silent swallow
- `from module import *` outside documented re-export
- `eval()` or `exec()` on non-constant input
- `Any` annotation without justifying comment
- Mutable default argument: `def f(x=[])`, `def f(x={})`
- `global` statement outside module-level init

ERROR — must fix before merge:
- Missing type annotations on any public function or method
- Missing docstring on any public class or function
- `if x == None:` (must be `if x is None:`)
- `if x == True:` (must be `if x:`)
- Lambda assigned to a name: `f = lambda x: x`
- `type(x) == Type` (must be `isinstance(x, Type)`)
- `if len(seq) == 0:` (must be `if not seq:`)
- Inconsistent returns (some explicit, some implicit)
- `raise Exception("msg")` — must use domain exception
- Tabs used for indentation

WARNING — should fix, document exception if not:
- Magic number without named constant
- Inline comment stating the obvious
- TODO without linked ticket or older than 30 days
- Missing `__all__` in public API module
- Trailing whitespace
- Import not at top of file without documented reason
