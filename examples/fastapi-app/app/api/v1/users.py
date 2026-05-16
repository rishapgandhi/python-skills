"""Users API endpoints — demonstrates standard CRUD patterns."""

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr

from app.core.exceptions import NotFoundError
from app.services.user_service import UserService

router = APIRouter()


class UserCreate(BaseModel):
    """Request schema for user creation."""

    email: EmailStr
    name: str


class UserResponse(BaseModel):
    """Response schema for a single user."""

    id: int
    email: str
    name: str


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate) -> UserResponse:
    """Create a new user."""
    user = await UserService.create(email=payload.email, name=payload.name)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    """Get a user by ID."""
    user = await UserService.get_by_id(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user
