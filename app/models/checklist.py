"""
Checklist models for migration planning.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base


class ChecklistStatus(str, enum.Enum):
    """Checklist status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChecklistCategory(str, enum.Enum):
    """Checklist item category enumeration."""
    PRE_DEPARTURE = "pre_departure"
    ARRIVAL = "arrival"
    SETUP = "setup"
    LEGAL = "legal"
    FINANCIAL = "financial"
    HEALTH = "health"
    EDUCATION = "education"
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class Checklist(Base):
    """Checklist model for migration planning."""
    
    __tablename__ = "checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Migration details
    origin_country_code = Column(String(3), nullable=False)
    destination_country_code = Column(String(3), nullable=False)
    reason_for_moving = Column(String(200), nullable=True)
    
    # Status and progress
    status = Column(Enum(ChecklistStatus), default=ChecklistStatus.DRAFT)
    progress_percentage = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="checklists")
    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Checklist(id={self.id}, title='{self.title}')>"


class ChecklistItem(Base):
    """Individual checklist item model."""
    
    __tablename__ = "checklist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)
    
    # Item details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ChecklistCategory), nullable=False)
    
    # Status and tracking
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Priority and ordering
    priority = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    
    # Additional metadata
    estimated_duration_days = Column(Integer, nullable=True)
    cost_estimate = Column(Integer, nullable=True)  # In cents
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    checklist = relationship("Checklist", back_populates="items")
    
    def __repr__(self) -> str:
        return f"<ChecklistItem(id={self.id}, title='{self.title}')>" 