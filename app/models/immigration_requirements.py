"""
Immigration requirements models for storing detailed immigration data.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base


class VisaType(str, enum.Enum):
    """Visa type enumeration."""
    TOURIST = "tourist"
    BUSINESS = "business"
    STUDENT = "student"
    WORK = "work"
    FAMILY = "family"
    INVESTOR = "investor"
    PERMANENT_RESIDENCE = "permanent_residence"
    CITIZENSHIP = "citizenship"
    OTHER = "other"


class ImmigrationRequirements(Base):
    """Immigration requirements model for storing detailed immigration data."""
    
    __tablename__ = "immigration_requirements"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(3), ForeignKey("countries.code"), nullable=False, index=True)
    
    # Visa information
    visa_type = Column(
        String(50),
        nullable=False,
        index=True
    )
    visa_category = Column(String(100), nullable=True)
    visa_subcategory = Column(String(100), nullable=True)
    
    # Requirements and fees
    requirements = Column(JSON, nullable=True)  # List of requirements
    required_documents = Column(JSON, nullable=True)  # List of required documents
    application_fee_usd = Column(Float, nullable=True)
    processing_time_days = Column(Integer, nullable=True)
    validity_period_days = Column(Integer, nullable=True)
    
    # Eligibility and restrictions
    eligibility_criteria = Column(JSON, nullable=True)  # List of eligibility criteria
    restrictions = Column(Text, nullable=True)
    age_requirements = Column(JSON, nullable=True)  # Min/max age if applicable
    language_requirements = Column(JSON, nullable=True)  # Language test requirements
    education_requirements = Column(JSON, nullable=True)  # Education level requirements
    work_experience_requirements = Column(JSON, nullable=True)  # Work experience requirements
    
    # Financial requirements
    financial_requirements = Column(JSON, nullable=True)  # Proof of funds, income requirements
    sponsorship_requirements = Column(JSON, nullable=True)  # Sponsor requirements if applicable
    
    # Health and security
    health_requirements = Column(JSON, nullable=True)  # Medical examination, insurance
    security_requirements = Column(JSON, nullable=True)  # Background checks, police certificates
    
    # Additional information
    application_process = Column(Text, nullable=True)
    interview_required = Column(Boolean, nullable=True)
    biometrics_required = Column(Boolean, nullable=True)
    medical_exam_required = Column(Boolean, nullable=True)
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(200), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_confidence_score = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="immigration_requirements")
    
    def __repr__(self) -> str:
        return f"<ImmigrationRequirements(country='{self.country_code}', visa_type='{self.visa_type}')>"


class CountryData(Base):
    """Additional country-specific data for migration planning."""
    
    __tablename__ = "country_data"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    country_code = Column(String(3), ForeignKey("countries.code"), nullable=False, index=True)
    
    # Driving and transportation
    driving_license_requirements = Column(JSON, nullable=True)
    vehicle_import_requirements = Column(JSON, nullable=True)
    public_transportation_info = Column(Text, nullable=True)
    
    # Pet regulations
    pet_import_requirements = Column(JSON, nullable=True)
    pet_quarantine_requirements = Column(JSON, nullable=True)
    restricted_pet_breeds = Column(JSON, nullable=True)
    
    # Language requirements
    official_languages = Column(JSON, nullable=True)  # List of official languages
    language_test_requirements = Column(JSON, nullable=True)
    language_schools_info = Column(Text, nullable=True)
    
    # Housing information
    housing_requirements = Column(JSON, nullable=True)
    rental_market_info = Column(Text, nullable=True)
    property_purchase_requirements = Column(JSON, nullable=True)
    
    # Healthcare information
    healthcare_system_info = Column(Text, nullable=True)
    health_insurance_requirements = Column(JSON, nullable=True)
    medical_facilities_info = Column(Text, nullable=True)
    
    # Education information
    education_system_info = Column(Text, nullable=True)
    school_enrollment_requirements = Column(JSON, nullable=True)
    university_admission_requirements = Column(JSON, nullable=True)
    
    # Banking and financial
    banking_requirements = Column(JSON, nullable=True)
    tax_obligations = Column(Text, nullable=True)
    investment_opportunities = Column(Text, nullable=True)
    
    # Cultural and social
    cultural_integration_info = Column(Text, nullable=True)
    community_resources = Column(Text, nullable=True)
    emergency_contacts = Column(JSON, nullable=True)
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(200), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_confidence_score = Column(Float, default=1.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="country_data")
    
    def __repr__(self) -> str:
        return f"<CountryData(country='{self.country_code}')>"


class ScrapingLog(Base):
    """Log for tracking scraping operations and their success/failure."""
    
    __tablename__ = "scraping_logs"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Scraping details
    country_code = Column(String(3), nullable=False, index=True)
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(500), nullable=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # 'full_scrape', 'update', 'verify'
    status = Column(String(50), nullable=False)  # 'success', 'failed', 'partial'
    
    # Results
    records_scraped = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Performance metrics
    duration_seconds = Column(Float, nullable=True)
    data_size_bytes = Column(Integer, nullable=True)
    
    # Metadata
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ScrapingLog(country='{self.country_code}', status='{self.status}')>"
