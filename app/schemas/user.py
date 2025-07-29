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
    age: Optional[int] = None
    marital_status: Optional[str] = None
    profession: Optional[str] = None
    dependents: int = 0
    origin_country_code: Optional[str] = None
    destination_country_code: Optional[str] = None
    reason_for_moving: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    profession: Optional[str] = None
    dependents: Optional[int] = None
    origin_country_code: Optional[str] = None
    destination_country_code: Optional[str] = None
    reason_for_moving: Optional[str] = None


class UserResponse(UserBase):
    """User response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserResponse):
    """User in database model (includes hashed password)."""
    hashed_password: str 