"""
Pydantic schemas for MCP Server API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DataCollectionRequest(BaseModel):
    """Request model for data collection."""
    country_codes: Optional[List[str]] = Field(
        default=None,
        description="List of country codes to collect data for. If None, collects for all supported countries."
    )
    run_in_background: bool = Field(
        default=False,
        description="Whether to run data collection in background"
    )


class PolicySummary(BaseModel):
    """Summary of immigration policies."""
    total_policies: int
    countries: List[str]
    policy_types: List[str]
    average_complexity: float
    average_cost_usd: Optional[float]
    average_duration_days: Optional[float]
    last_updated: str


class DataCollectionResponse(BaseModel):
    """Response model for data collection."""
    status: str
    countries_processed: List[str]
    total_policies: int
    summary: PolicySummary
    message: str


class NormalizedPolicyResponse(BaseModel):
    """Response model for normalized policy data."""
    title: str
    policy_type: str
    description: str
    requirements: List[str]
    estimated_duration_days: Optional[int]
    estimated_cost_usd: Optional[float]
    complexity_score: int
    eligibility_criteria: List[str]
    documents_required: List[str]
    source_url: str


class CountryDataResponse(BaseModel):
    """Response model for country-specific data."""
    country_code: str
    country_name: str
    policies_count: int
    policies: List[NormalizedPolicyResponse]
    last_updated: Optional[datetime]
    data_sources: List[Dict[str, Any]]


class PolicyChangeDetail(BaseModel):
    """Details of a policy change."""
    country_code: str
    change_type: str
    changes_count: Optional[int]
    changed_policies: Optional[List[str]]
    policies_count: Optional[int]


class PolicyChangeResponse(BaseModel):
    """Response model for policy change detection."""
    status: str
    changes_detected: int
    change_details: List[PolicyChangeDetail]
    message: str


class DataCollectionStatusResponse(BaseModel):
    """Response model for data collection status."""
    status: str
    latest_update: Optional[str]
    data_files_count: Optional[int]
    global_summary: Optional[Dict[str, Any]]
    message: Optional[str]
    error: Optional[str]


class SupportedCountriesResponse(BaseModel):
    """Response model for supported countries."""
    countries: List[str]
    country_details: Dict[str, Dict[str, Any]]
    total_countries: int


class CountryDetail(BaseModel):
    """Details of a supported country."""
    name: str
    sources_count: int
    sources: List[str]


class MCPHealthResponse(BaseModel):
    """Response model for MCP server health check."""
    status: str
    supported_countries: int
    last_data_collection: Optional[str]
    data_sources_available: bool
    message: str 