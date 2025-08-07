"""
User schemas for request/response models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """Base user model."""
    email: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    onboarding_complete: Optional[bool] = None


class UserResponse(UserBase):
    """User response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str  # UUID
    cognito_sub: str
    onboarding_complete: bool
    last_login: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserResponse):
    """User in database model."""
    pass 