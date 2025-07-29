"""
Policy model for storing immigration policies and requirements.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base


class PolicyType(str, enum.Enum):
    """Policy type enumeration."""
    VISA_REQUIREMENT = "visa_requirement"
    DOCUMENT_REQUIREMENT = "document_requirement"
    HEALTH_REQUIREMENT = "health_requirement"
    FINANCIAL_REQUIREMENT = "financial_requirement"
    BACKGROUND_CHECK = "background_check"
    LANGUAGE_REQUIREMENT = "language_requirement"
    EDUCATION_REQUIREMENT = "education_requirement"
    WORK_PERMIT = "work_permit"
    RESIDENCE_PERMIT = "residence_permit"
    CITIZENSHIP = "citizenship"
    OTHER = "other"


class PolicyStatus(str, enum.Enum):
    """Policy status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"


class Policy(Base):
    """Policy model for immigration policies and requirements."""
    
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), ForeignKey("countries.code"), nullable=False)
    
    # Policy details
    policy_type = Column(Enum(PolicyType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)  # JSON string of requirements
    
    # Requirements and costs
    processing_time_days = Column(Integer, nullable=True)
    application_fee_usd = Column(Integer, nullable=True)  # In cents
    validity_period_days = Column(Integer, nullable=True)
    
    # Eligibility
    eligibility_criteria = Column(Text, nullable=True)  # JSON string
    required_documents = Column(Text, nullable=True)  # JSON string
    restrictions = Column(Text, nullable=True)  # JSON string
    
    # Status and dates
    status = Column(Enum(PolicyStatus), default=PolicyStatus.ACTIVE)
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(200), nullable=True)
    last_verified = Column(DateTime, nullable=True)
    
    # Metadata
    priority = Column(Integer, default=1)
    is_mandatory = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    country = relationship("Country")
    
    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, title='{self.title}', country='{self.country_code}')>" 