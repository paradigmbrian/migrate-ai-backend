"""
Data Collection API endpoints for immigration data collection and policy monitoring.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.immigration_data_collector import ImmigrationDataCollector
from app.services.data_normalizer import DataNormalizer
from app.services.cron_service import CronService
from app.schemas.mcp import (
    DataCollectionRequest,
    DataCollectionResponse,
    PolicyChangeResponse,
    CountryDataResponse,
    DataCollectionStatusResponse,
    SupportedCountriesResponse
)

router = APIRouter()


@router.get("/supported-countries", response_model=SupportedCountriesResponse)
async def get_supported_countries(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of supported countries for data collection."""
    try:
        async with ImmigrationDataCollector() as data_collector:
            countries = await data_collector.get_supported_countries()
            
            # Get detailed info for each country
            country_details = {}
            for country_code in countries:
                info = await data_collector.get_data_source_info(country_code)
                if info:
                    country_details[country_code] = {
                        'name': info['name'],
                        'sources_count': len(info['sources']),
                        'sources': [source['name'] for source in info['sources']]
                    }
            
            return SupportedCountriesResponse(
                countries=countries,
                country_details=country_details,
                total_countries=len(countries)
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving supported countries: {str(e)}"
        )


@router.post("/collect-data", response_model=DataCollectionResponse)
async def collect_immigration_data(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Collect immigration data for specified countries."""
    try:
        async with ImmigrationDataCollector() as data_collector:
            # Collect data for specified countries
            scraped_data = await data_collector.collect_data(request.country_codes)
            
            # Normalize the data
            normalizer = DataNormalizer()
            all_normalized_policies = []
            
            for country_code, data in scraped_data.items():
                normalized_policies = normalizer.normalize_policies(data.policies)
                all_normalized_policies.extend(normalized_policies)
            
            # Generate summary
            summary = normalizer.get_policy_summary(all_normalized_policies)
            
            # If requested, run in background
            if request.run_in_background:
                background_tasks.add_task(
                    _save_collected_data,
                    scraped_data,
                    all_normalized_policies,
                    summary
                )
            
            return DataCollectionResponse(
                status="success",
                countries_processed=list(scraped_data.keys()),
                total_policies=len(all_normalized_policies),
                summary=summary,
                message="Data collection completed successfully"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting immigration data: {str(e)}"
        )


@router.get("/country/{country_code}", response_model=CountryDataResponse)
async def get_country_data(
    country_code: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get immigration data for a specific country."""
    try:
        async with ImmigrationDataCollector() as data_collector:
            # Verify country is supported
            supported_countries = await data_collector.get_supported_countries()
            if country_code not in supported_countries:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Country {country_code} not supported"
                )
            
            # Collect data for the country
            scraped_data = await data_collector.collect_data([country_code])
            
            if country_code not in scraped_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to collect data for {country_code}"
                )
            
            # Normalize the data
            normalizer = DataNormalizer()
            normalized_policies = normalizer.normalize_policies(scraped_data[country_code].policies)
            
            # Get country info
            country_info = await data_collector.get_data_source_info(country_code)
            
            return CountryDataResponse(
                country_code=country_code,
                country_name=country_info['name'] if country_info else country_code,
                policies_count=len(normalized_policies),
                policies=normalized_policies,
                last_updated=scraped_data[country_code].policies[0].last_updated if scraped_data[country_code].policies else None,
                data_sources=country_info['sources'] if country_info else []
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving data for {country_code}: {str(e)}"
        )


@router.post("/detect-changes", response_model=PolicyChangeResponse)
async def detect_policy_changes(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Detect changes in immigration policies."""
    try:
        cron_service = CronService()
        
        # Run policy change detection
        result = await cron_service.run_policy_change_detection()
        
        if result['status'] == 'warning':
            return PolicyChangeResponse(
                status="warning",
                message=result['message'],
                changes_detected=0,
                change_details=[]
            )
        
        if result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
        return PolicyChangeResponse(
            status="success",
            changes_detected=result['changes_detected'],
            change_details=result['change_details'],
            message=f"Policy change detection completed. Found {result['changes_detected']} changes."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting policy changes: {str(e)}"
        )


@router.post("/run-daily-collection")
async def run_daily_data_collection(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run daily data collection task."""
    try:
        cron_service = CronService()
        
        # Run daily collection in background
        background_tasks.add_task(cron_service.run_daily_data_collection)
        
        return {
            "status": "success",
            "message": "Daily data collection started in background"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting daily data collection: {str(e)}"
        )


@router.post("/run-weekly-collection")
async def run_weekly_data_collection(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run weekly comprehensive data collection task."""
    try:
        cron_service = CronService()
        
        # Run weekly collection in background
        background_tasks.add_task(cron_service.run_weekly_data_collection)
        
        return {
            "status": "success",
            "message": "Weekly data collection started in background"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting weekly data collection: {str(e)}"
        )


@router.get("/collection-status", response_model=DataCollectionStatusResponse)
async def get_data_collection_status(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the status of data collection."""
    try:
        cron_service = CronService()
        status_info = await cron_service.get_data_collection_status()
        
        return DataCollectionStatusResponse(**status_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving data collection status: {str(e)}"
        )


async def _save_collected_data(
    scraped_data: Dict[str, Any],
    normalized_policies: List[Any],
    summary: Dict[str, Any]
):
    """Background task to save collected data."""
    try:
        cron_service = CronService()
        
        # Save country-specific data
        for country_code, data in scraped_data.items():
            country_policies = [p for p in normalized_policies if p.country_code == country_code]
            await cron_service._save_country_data(country_code, country_policies)
        
        # Save global summary
        await cron_service._save_global_summary(summary)
        
    except Exception as e:
        # Log error but don't raise - this is a background task
        print(f"Error saving collected data: {str(e)}") 