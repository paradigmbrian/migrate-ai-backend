"""
Authentication schemas for request/response models.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None


class UserCreate(BaseModel):
    """User creation request model."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    age: Optional[int] = None
    marital_status: Optional[str] = None
    profession: Optional[str] = None
    dependents: int = 0
    origin_country_code: Optional[str] = None
    destination_country_code: Optional[str] = None
    reason_for_moving: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str 