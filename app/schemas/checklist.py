"""
Checklist Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from app.models.checklist import ChecklistStatus, ChecklistCategory


# Base schemas
class ChecklistItemBase(BaseModel):
    """Base checklist item schema."""
    title: str = Field(..., min_length=1, max_length=200, description="Item title")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    category: ChecklistCategory = Field(..., description="Item category")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1-5)")
    order_index: int = Field(0, ge=0, description="Display order")
    estimated_duration_days: Optional[int] = Field(None, ge=0, description="Estimated duration in days")
    cost_estimate: Optional[int] = Field(None, ge=0, description="Cost estimate in cents")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    due_date: Optional[datetime] = Field(None, description="Due date")


class ChecklistBase(BaseModel):
    """Base checklist schema."""
    title: str = Field(..., min_length=1, max_length=200, description="Checklist title")
    description: Optional[str] = Field(None, max_length=1000, description="Checklist description")
    origin_country_code: str = Field(..., min_length=2, max_length=3, description="Origin country code")
    destination_country_code: str = Field(..., min_length=2, max_length=3, description="Destination country code")
    reason_for_moving: Optional[str] = Field(None, max_length=200, description="Reason for moving")


# Request schemas
class ChecklistItemCreate(ChecklistItemBase):
    """Schema for creating a checklist item."""
    pass


class ChecklistItemUpdate(BaseModel):
    """Schema for updating a checklist item."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[ChecklistCategory] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    order_index: Optional[int] = Field(None, ge=0)
    estimated_duration_days: Optional[int] = Field(None, ge=0)
    cost_estimate: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None


class ChecklistCreate(ChecklistBase):
    """Schema for creating a checklist."""
    items: Optional[List[ChecklistItemCreate]] = Field(default_factory=list, description="Initial checklist items")


class ChecklistUpdate(BaseModel):
    """Schema for updating a checklist."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    origin_country_code: Optional[str] = Field(None, min_length=2, max_length=3)
    destination_country_code: Optional[str] = Field(None, min_length=2, max_length=3)
    reason_for_moving: Optional[str] = Field(None, max_length=200)
    status: Optional[ChecklistStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)


class ChecklistGenerateRequest(BaseModel):
    """Schema for checklist generation request."""
    origin_country_code: str = Field(..., min_length=2, max_length=3, description="Origin country code")
    destination_country_code: str = Field(..., min_length=2, max_length=3, description="Destination country code")
    reason_for_moving: Optional[str] = Field(None, max_length=200, description="Reason for moving")
    user_profile: Optional[dict] = Field(default_factory=dict, description="User profile data for personalization")
    
    @validator('origin_country_code', 'destination_country_code')
    def validate_country_codes(cls, v):
        """Validate country codes are different."""
        return v.upper()


# Response schemas
class ChecklistItemResponse(ChecklistItemBase):
    """Schema for checklist item response."""
    id: str
    checklist_id: str
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChecklistResponse(ChecklistBase):
    """Schema for checklist response."""
    id: str
    user_id: str
    status: ChecklistStatus
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    items: List[ChecklistItemResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChecklistSummary(BaseModel):
    """Schema for checklist summary (list view)."""
    id: str
    title: str
    origin_country_code: str
    destination_country_code: str
    status: ChecklistStatus
    progress_percentage: int
    total_items: int
    completed_items: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChecklistProgressUpdate(BaseModel):
    """Schema for checklist progress update."""
    checklist_id: int
    progress_percentage: int = Field(..., ge=0, le=100)
    completed_items: int = Field(..., ge=0)
    total_items: int = Field(..., ge=0)
    updated_at: datetime


class ChecklistGenerationResponse(BaseModel):
    """Schema for checklist generation response."""
    checklist: ChecklistResponse
    generated_items_count: int
    estimated_completion_days: int
    total_estimated_cost: Optional[int] = Field(None, description="Total estimated cost in cents")
    message: str = "Checklist generated successfully"


# Error schemas
class ChecklistError(BaseModel):
    """Schema for checklist error responses."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationError(BaseModel):
    """Schema for validation error responses."""
    error: str = "Validation Error"
    detail: List[dict]
    code: str = "VALIDATION_ERROR" 