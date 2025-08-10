"""
Pydantic schemas for immigration requirements data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ImmigrationRequirementsBase(BaseModel):
    """Base schema for immigration requirements."""
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    visa_type: str = Field(..., description="Type of visa")
    visa_category: Optional[str] = Field(None, description="Visa category")
    visa_subcategory: Optional[str] = Field(None, description="Visa subcategory")
    requirements: Optional[List[str]] = Field(None, description="List of requirements")
    required_documents: Optional[List[str]] = Field(None, description="List of required documents")
    application_fee_usd: Optional[float] = Field(None, description="Application fee in USD")
    processing_time_days: Optional[int] = Field(None, description="Processing time in days")
    validity_period_days: Optional[int] = Field(None, description="Validity period in days")
    eligibility_criteria: Optional[List[str]] = Field(None, description="List of eligibility criteria")
    restrictions: Optional[str] = Field(None, description="Restrictions")
    age_requirements: Optional[Dict[str, Any]] = Field(None, description="Age requirements")
    language_requirements: Optional[Dict[str, Any]] = Field(None, description="Language requirements")
    education_requirements: Optional[Dict[str, Any]] = Field(None, description="Education requirements")
    work_experience_requirements: Optional[Dict[str, Any]] = Field(None, description="Work experience requirements")
    financial_requirements: Optional[Dict[str, Any]] = Field(None, description="Financial requirements")
    sponsorship_requirements: Optional[Dict[str, Any]] = Field(None, description="Sponsorship requirements")
    health_requirements: Optional[Dict[str, Any]] = Field(None, description="Health requirements")
    security_requirements: Optional[Dict[str, Any]] = Field(None, description="Security requirements")
    application_process: Optional[str] = Field(None, description="Application process description")
    interview_required: Optional[bool] = Field(None, description="Whether interview is required")
    biometrics_required: Optional[bool] = Field(None, description="Whether biometrics are required")
    medical_exam_required: Optional[bool] = Field(None, description="Whether medical exam is required")
    source_url: Optional[str] = Field(None, description="Source URL")
    source_name: Optional[str] = Field(None, description="Source name")
    data_confidence_score: Optional[float] = Field(1.0, description="Data confidence score (0.0 to 1.0)")
    is_active: Optional[bool] = Field(True, description="Whether the requirement is active")
    is_verified: Optional[bool] = Field(False, description="Whether the data has been verified")


class ImmigrationRequirementsCreate(ImmigrationRequirementsBase):
    """Schema for creating immigration requirements."""
    pass


class ImmigrationRequirementsUpdate(BaseModel):
    """Schema for updating immigration requirements."""
    visa_category: Optional[str] = None
    visa_subcategory: Optional[str] = None
    requirements: Optional[List[str]] = None
    required_documents: Optional[List[str]] = None
    application_fee_usd: Optional[float] = None
    processing_time_days: Optional[int] = None
    validity_period_days: Optional[int] = None
    eligibility_criteria: Optional[List[str]] = None
    restrictions: Optional[str] = None
    age_requirements: Optional[Dict[str, Any]] = None
    language_requirements: Optional[Dict[str, Any]] = None
    education_requirements: Optional[Dict[str, Any]] = None
    work_experience_requirements: Optional[Dict[str, Any]] = None
    financial_requirements: Optional[Dict[str, Any]] = None
    sponsorship_requirements: Optional[Dict[str, Any]] = None
    health_requirements: Optional[Dict[str, Any]] = None
    security_requirements: Optional[Dict[str, Any]] = None
    application_process: Optional[str] = None
    interview_required: Optional[bool] = None
    biometrics_required: Optional[bool] = None
    medical_exam_required: Optional[bool] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    data_confidence_score: Optional[float] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class ImmigrationRequirements(ImmigrationRequirementsBase):
    """Schema for immigration requirements response."""
    id: str
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CountryDataBase(BaseModel):
    """Base schema for country data."""
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    driving_license_requirements: Optional[Dict[str, Any]] = Field(None, description="Driving license requirements")
    vehicle_import_requirements: Optional[Dict[str, Any]] = Field(None, description="Vehicle import requirements")
    public_transportation_info: Optional[str] = Field(None, description="Public transportation information")
    pet_import_requirements: Optional[Dict[str, Any]] = Field(None, description="Pet import requirements")
    pet_quarantine_requirements: Optional[Dict[str, Any]] = Field(None, description="Pet quarantine requirements")
    restricted_pet_breeds: Optional[List[str]] = Field(None, description="Restricted pet breeds")
    official_languages: Optional[List[str]] = Field(None, description="Official languages")
    language_test_requirements: Optional[Dict[str, Any]] = Field(None, description="Language test requirements")
    language_schools_info: Optional[str] = Field(None, description="Language schools information")
    housing_requirements: Optional[Dict[str, Any]] = Field(None, description="Housing requirements")
    rental_market_info: Optional[str] = Field(None, description="Rental market information")
    property_purchase_requirements: Optional[Dict[str, Any]] = Field(None, description="Property purchase requirements")
    healthcare_system_info: Optional[str] = Field(None, description="Healthcare system information")
    health_insurance_requirements: Optional[Dict[str, Any]] = Field(None, description="Health insurance requirements")
    medical_facilities_info: Optional[str] = Field(None, description="Medical facilities information")
    education_system_info: Optional[str] = Field(None, description="Education system information")
    school_enrollment_requirements: Optional[Dict[str, Any]] = Field(None, description="School enrollment requirements")
    university_admission_requirements: Optional[Dict[str, Any]] = Field(None, description="University admission requirements")
    banking_requirements: Optional[Dict[str, Any]] = Field(None, description="Banking requirements")
    tax_obligations: Optional[str] = Field(None, description="Tax obligations")
    investment_opportunities: Optional[str] = Field(None, description="Investment opportunities")
    cultural_integration_info: Optional[str] = Field(None, description="Cultural integration information")
    community_resources: Optional[str] = Field(None, description="Community resources")
    emergency_contacts: Optional[Dict[str, Any]] = Field(None, description="Emergency contacts")
    source_url: Optional[str] = Field(None, description="Source URL")
    source_name: Optional[str] = Field(None, description="Source name")
    data_confidence_score: Optional[float] = Field(1.0, description="Data confidence score (0.0 to 1.0)")
    is_active: Optional[bool] = Field(True, description="Whether the data is active")
    is_verified: Optional[bool] = Field(False, description="Whether the data has been verified")


class CountryDataCreate(CountryDataBase):
    """Schema for creating country data."""
    pass


class CountryDataUpdate(BaseModel):
    """Schema for updating country data."""
    driving_license_requirements: Optional[Dict[str, Any]] = None
    vehicle_import_requirements: Optional[Dict[str, Any]] = None
    public_transportation_info: Optional[str] = None
    pet_import_requirements: Optional[Dict[str, Any]] = None
    pet_quarantine_requirements: Optional[Dict[str, Any]] = None
    restricted_pet_breeds: Optional[List[str]] = None
    official_languages: Optional[List[str]] = None
    language_test_requirements: Optional[Dict[str, Any]] = None
    language_schools_info: Optional[str] = None
    housing_requirements: Optional[Dict[str, Any]] = None
    rental_market_info: Optional[str] = None
    property_purchase_requirements: Optional[Dict[str, Any]] = None
    healthcare_system_info: Optional[str] = None
    health_insurance_requirements: Optional[Dict[str, Any]] = None
    medical_facilities_info: Optional[str] = None
    education_system_info: Optional[str] = None
    school_enrollment_requirements: Optional[Dict[str, Any]] = None
    university_admission_requirements: Optional[Dict[str, Any]] = None
    banking_requirements: Optional[Dict[str, Any]] = None
    tax_obligations: Optional[str] = None
    investment_opportunities: Optional[str] = None
    cultural_integration_info: Optional[str] = None
    community_resources: Optional[str] = None
    emergency_contacts: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    data_confidence_score: Optional[float] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class CountryData(CountryDataBase):
    """Schema for country data response."""
    id: str
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScrapingLogBase(BaseModel):
    """Base schema for scraping logs."""
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    source_name: str = Field(..., description="Name of the data source")
    source_url: Optional[str] = Field(None, description="Source URL")
    operation_type: str = Field(..., description="Type of operation")
    status: str = Field(..., description="Status of the operation")
    records_scraped: Optional[int] = Field(0, description="Number of records scraped")
    records_updated: Optional[int] = Field(0, description="Number of records updated")
    records_failed: Optional[int] = Field(0, description="Number of records that failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    duration_seconds: Optional[float] = Field(None, description="Duration of the operation in seconds")
    data_size_bytes: Optional[int] = Field(None, description="Size of scraped data in bytes")
    user_agent: Optional[str] = Field(None, description="User agent used for scraping")
    ip_address: Optional[str] = Field(None, description="IP address used for scraping")


class ScrapingLogCreate(ScrapingLogBase):
    """Schema for creating scraping logs."""
    pass


class ScrapingLog(ScrapingLogBase):
    """Schema for scraping log response."""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ScrapingResult(BaseModel):
    """Schema for scraping operation result."""
    success: bool
    country_code: str
    records_scraped: int
    records_updated: int
    records_failed: int
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    data_size_bytes: Optional[int] = None


class AdminScrapingTrigger(BaseModel):
    """Schema for triggering scraping operations."""
    country_code: Optional[str] = Field(None, description="Country code to scrape (if not provided, scrapes all)")
    force: Optional[bool] = Field(False, description="Force scraping even if already in progress")


class AdminDataSummary(BaseModel):
    """Schema for admin data summary."""
    total_requirements: int
    requirements_by_country: List[Dict[str, Any]]
    requirements_by_visa_type: List[Dict[str, Any]]
    data_freshness: List[Dict[str, Any]]


class AdminScrapingStatus(BaseModel):
    """Schema for admin scraping status."""
    scraping_logs: List[Dict[str, Any]]
    total_logs: int
