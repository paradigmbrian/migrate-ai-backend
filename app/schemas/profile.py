"""
Profile schemas for request/response models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, validator
import re


class ProfileResponse(BaseModel):
    """Profile response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    cognito_sub: str
    email: str
    first_name: str
    last_name: str
    birthdate: Optional[str] = None
    onboarding_complete: bool
    last_login: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    """Profile update request model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[str] = None
    
    @validator('first_name')
    def validate_first_name(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("First name cannot be empty")
            if len(v) > 100:
                raise ValueError("First name cannot exceed 100 characters")
        return v.strip() if v else v
    
    @validator('last_name')
    def validate_last_name(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("Last name cannot be empty")
            if len(v) > 100:
                raise ValueError("Last name cannot exceed 100 characters")
        return v.strip() if v else v
    
    @validator('birthdate')
    def validate_birthdate(cls, v):
        if v is not None:
            # Validate YYYY-MM-DD format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("Birthdate must be in YYYY-MM-DD format")
            
            # Validate reasonable date range (1900 to current year)
            try:
                from datetime import datetime
                birth_date = datetime.strptime(v, '%Y-%m-%d')
                current_year = datetime.now().year
                
                if birth_date.year < 1900 or birth_date.year > current_year:
                    raise ValueError(f"Birthdate year must be between 1900 and {current_year}")
                    
                # Check if date is in the future
                if birth_date > datetime.now():
                    raise ValueError("Birthdate cannot be in the future")
                    
            except ValueError as e:
                if "Birthdate year" in str(e) or "Birthdate cannot be" in str(e):
                    raise e
                raise ValueError("Invalid birthdate format")
                
        return v


class ProfileStatus(BaseModel):
    """Profile completion status model."""
    completion_percentage: int
    completed_fields: List[str]
    missing_fields: List[str]
    total_fields: int
    is_complete: bool
    suggestions: List[str]
    
    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Completion percentage must be between 0 and 100")
        return v 