"""
Admin endpoints for managing immigration data collection and scraping operations.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.api.deps import get_admin_user_by_token, get_db
from app.services.enhanced_immigration_data_collector import EnhancedImmigrationDataCollector
from app.models.immigration_requirements import ImmigrationRequirements, CountryData, ScrapingLog

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/trigger-scrape/{country_code}")
async def trigger_scrape_country(
    country_code: str,
    background_tasks: BackgroundTasks,
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger scraping for a specific country.
    Only accessible by admin users.
    """
    try:
        # Validate country code
        if len(country_code) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country code must be 2 characters (ISO 3166-1 alpha-2)"
            )
        
        # Convert to uppercase
        country_code = country_code.upper()
        
        # Check if scraping is already in progress
        stmt = select(ScrapingLog).where(
            ScrapingLog.country_code == country_code,
            ScrapingLog.status == "running"
        )
        result = await db.execute(stmt)
        running_scrape = result.scalar_one_or_none()
        
        if running_scrape:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scraping already in progress for {country_code}"
            )
        
        # Add scraping task to background
        background_tasks.add_task(
            _scrape_country_background,
            db,
            country_code,
            admin_user['user_sub']
        )
        
        return {
            "success": True,
            "message": f"Scraping started for {country_code}",
            "country_code": country_code,
            "triggered_by": admin_user['user_sub']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering scrape for {country_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger scraping operation"
        )


@router.post("/trigger-scrape-all")
async def trigger_scrape_all_countries(
    background_tasks: BackgroundTasks,
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger scraping for all supported countries.
    Only accessible by admin users.
    """
    try:
        async with EnhancedImmigrationDataCollector() as collector:
            supported_countries = await collector.get_supported_countries()
        
        # Check for running scrapes
        stmt = select(ScrapingLog).where(ScrapingLog.status == "running")
        result = await db.execute(stmt)
        running_scrapes = result.scalars().all()
        
        if running_scrapes:
            running_countries = [log.country_code for log in running_scrapes]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scraping already in progress for: {', '.join(running_countries)}"
            )
        
        # Add scraping tasks to background for all countries
        for country_code in supported_countries:
            background_tasks.add_task(
                _scrape_country_background,
                db,
                country_code,
                admin_user['user_sub']
            )
        
        return {
            "success": True,
            "message": f"Scraping started for {len(supported_countries)} countries",
            "countries": supported_countries,
            "triggered_by": admin_user['user_sub']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering scrape for all countries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger scraping operations"
        )


@router.get("/scraping-status")
async def get_scraping_status(
    country_code: Optional[str] = None,
    limit: int = 50,
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get scraping status and history.
    Only accessible by admin users.
    """
    try:
        async with EnhancedImmigrationDataCollector() as collector:
            status_data = await collector.get_scraping_status(db, country_code)
        
        # Limit results
        status_data = status_data[:limit]
        
        return {
            "success": True,
            "scraping_logs": status_data,
            "total_logs": len(status_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scraping status"
        )


@router.get("/data-summary")
async def get_data_summary(
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of immigration data in the database.
    Only accessible by admin users.
    """
    try:
        # Get counts for immigration requirements
        stmt = select(func.count(ImmigrationRequirements.id))
        result = await db.execute(stmt)
        total_requirements = result.scalar()
        
        # Get counts by country
        stmt = select(
            ImmigrationRequirements.country_code,
            func.count(ImmigrationRequirements.id).label('count')
        ).group_by(ImmigrationRequirements.country_code)
        result = await db.execute(stmt)
        requirements_by_country = [
            {"country_code": row.country_code, "count": row.count}
            for row in result.fetchall()
        ]
        
        # Get counts by visa type
        stmt = select(
            ImmigrationRequirements.visa_type,
            func.count(ImmigrationRequirements.id).label('count')
        ).group_by(ImmigrationRequirements.visa_type)
        result = await db.execute(stmt)
        requirements_by_visa_type = [
            {"visa_type": row.visa_type, "count": row.count}
            for row in result.fetchall()
        ]
        
        # Get data freshness
        stmt = select(
            ImmigrationRequirements.country_code,
            func.max(ImmigrationRequirements.last_updated).label('last_updated')
        ).group_by(ImmigrationRequirements.country_code)
        result = await db.execute(stmt)
        data_freshness = [
            {
                "country_code": row.country_code,
                "last_updated": row.last_updated.isoformat() if row.last_updated else None
            }
            for row in result.fetchall()
        ]
        
        return {
            "success": True,
            "summary": {
                "total_requirements": total_requirements,
                "requirements_by_country": requirements_by_country,
                "requirements_by_visa_type": requirements_by_visa_type,
                "data_freshness": data_freshness
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting data summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data summary"
        )


@router.get("/supported-countries")
async def get_supported_countries(
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token)
):
    """
    Get list of supported countries for scraping.
    Only accessible by admin users.
    """
    try:
        async with EnhancedImmigrationDataCollector() as collector:
            countries = await collector.get_supported_countries()
        
        return {
            "success": True,
            "supported_countries": countries,
            "total_countries": len(countries)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported countries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported countries"
        )


@router.delete("/clear-data/{country_code}")
async def clear_country_data(
    country_code: str,
    admin_user: Dict[str, Any] = Depends(get_admin_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all immigration data for a specific country.
    Only accessible by admin users.
    """
    try:
        # Validate country code
        if len(country_code) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country code must be 2 characters (ISO 3166-1 alpha-2)"
            )
        
        country_code = country_code.upper()
        
        # Delete immigration requirements
        stmt = delete(ImmigrationRequirements).where(
            ImmigrationRequirements.country_code == country_code
        )
        result = await db.execute(stmt)
        requirements_deleted = result.rowcount
        
        # Delete country data
        stmt = delete(CountryData).where(
            CountryData.country_code == country_code
        )
        result = await db.execute(stmt)
        country_data_deleted = result.rowcount
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Data cleared for {country_code}",
            "country_code": country_code,
            "requirements_deleted": requirements_deleted,
            "country_data_deleted": country_data_deleted,
            "cleared_by": admin_user['user_sub']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing data for {country_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear country data"
        )


async def _scrape_country_background(db: AsyncSession, country_code: str, user_sub: str):
    """
    Background task for scraping country data.
    """
    try:
        logger.info(f"Starting background scrape for {country_code}")
        
        async with EnhancedImmigrationDataCollector() as collector:
            result = await collector.scrape_country_data(db, country_code)
        
        if result.success:
            logger.info(f"Successfully scraped {result.records_scraped} records for {country_code}")
        else:
            logger.error(f"Failed to scrape data for {country_code}: {result.error_message}")
            
    except Exception as e:
        logger.error(f"Error in background scraping for {country_code}: {e}")
