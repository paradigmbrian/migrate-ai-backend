"""
Pydantic schemas for request/response models.
"""

from .immigration import (
    ImmigrationRequirements,
    ImmigrationRequirementsCreate,
    ImmigrationRequirementsUpdate,
    CountryData,
    CountryDataCreate,
    CountryDataUpdate,
    ScrapingLog,
    ScrapingLogCreate,
    ScrapingResult,
    AdminScrapingTrigger,
    AdminDataSummary,
    AdminScrapingStatus
)

__all__ = [
    "ImmigrationRequirements",
    "ImmigrationRequirementsCreate", 
    "ImmigrationRequirementsUpdate",
    "CountryData",
    "CountryDataCreate",
    "CountryDataUpdate",
    "ScrapingLog",
    "ScrapingLogCreate",
    "ScrapingResult",
    "AdminScrapingTrigger",
    "AdminDataSummary",
    "AdminScrapingStatus"
] 