"""User business logic — service layer."""

import structlog

logger = structlog.get_logger()

# In-memory store for example simplicity. Production uses repository pattern with SQLAlchemy.
_USERS: dict[int, dict] = {}
_NEXT_ID = 1


class UserService:
    """User domain operations."""

    @staticmethod
    async def create(email: str, name: str) -> dict:
        """Create a new user."""
        global _NEXT_ID
        user = {"id": _NEXT_ID, "email": email, "name": name}
        _USERS[_NEXT_ID] = user
        logger.info("user_created", user_id=_NEXT_ID, email=email)
        _NEXT_ID += 1
        return user

    @staticmethod
    async def get_by_id(user_id: int) -> dict | None:
        """Retrieve user by ID. Returns None if not found."""
        return _USERS.get(user_id)
