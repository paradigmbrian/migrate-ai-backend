"""
Policy monitoring endpoints for automated policy change detection and notifications.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.services.policy_monitoring_service import PolicyMonitoringService
from app.api.deps import get_current_user

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check-changes", response_model=Dict[str, Any])
async def check_for_policy_changes(
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger a check for policy changes across all monitored countries.
    """
    logger.info("Manual policy change check triggered")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        result = await monitoring_service.check_for_policy_changes()
        
        if result['success']:
            return {
                "message": "Policy change check completed",
                "changes_detected": result['changes_detected'],
                "last_check": result['last_check']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Policy change check failed: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error checking for policy changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for policy changes"
        )


@router.get("/user-changes", response_model=Dict[str, Any])
async def get_policy_changes_for_user(
    days_back: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get policy changes relevant to the current user.
    """
    logger.info(f"Getting policy changes for user {current_user.id}")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        result = await monitoring_service.get_policy_changes_for_user(
            current_user, days_back
        )
        
        if result['success']:
            return {
                "message": "Policy changes retrieved successfully",
                "policy_changes": result['policy_changes'],
                "impact_assessment": result['impact_assessment'],
                "relevant_countries": result['relevant_countries']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get policy changes: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error getting policy changes for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get policy changes"
        )


@router.post("/assess-impact", response_model=Dict[str, Any])
async def assess_policy_change_impact(
    policy_change: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assess the impact of a specific policy change on user checklists.
    """
    logger.info(f"Assessing policy change impact for user {current_user.id}")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        
        # Get user's checklists (this would typically come from a checklist service)
        user_checklists = []  # Placeholder - would get actual checklists
        
        result = await monitoring_service.assess_policy_change_impact(
            policy_change, user_checklists
        )
        
        return {
            "message": "Impact assessment completed",
            "impact_analysis": result
        }
        
    except Exception as e:
        logger.error(f"Error assessing policy change impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assess policy change impact"
        )


@router.get("/notification-preferences", response_model=Dict[str, Any])
async def get_user_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notification preferences for policy changes.
    """
    logger.info(f"Getting notification preferences for user {current_user.id}")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        preferences = await monitoring_service.get_user_notification_preferences(current_user.id)
        
        return {
            "message": "Notification preferences retrieved successfully",
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/notification-preferences", response_model=Dict[str, Any])
async def update_user_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's notification preferences for policy changes.
    """
    logger.info(f"Updating notification preferences for user {current_user.id}")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        result = await monitoring_service.update_user_notification_preferences(
            current_user.id, preferences
        )
        
        if result['success']:
            return {
                "message": "Notification preferences updated successfully",
                "preferences": result['preferences']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update preferences: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.get("/monitoring-status", response_model=Dict[str, Any])
async def get_monitoring_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current status of the policy monitoring system.
    """
    logger.info("Getting policy monitoring status")
    
    try:
        monitoring_service = PolicyMonitoringService(db)
        
        return {
            "message": "Policy monitoring status retrieved",
            "status": {
                "monitoring_active": True,
                "last_check": monitoring_service.last_check.isoformat(),
                "monitoring_interval_hours": monitoring_service.monitoring_interval // 3600,
                "countries_monitored": len(await monitoring_service._get_active_countries())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring status"
        )


@router.post("/test-policy-monitoring", response_model=Dict[str, Any])
async def test_policy_monitoring_features(
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint for policy monitoring features without authentication.
    This is for testing purposes only.
    """
    logger.info("Testing policy monitoring features")
    
    try:
        # Create a mock user for testing
        from app.models.user import User
        
        mock_user = User(
            id="test-user-123",
            cognito_sub="test-cognito-sub",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            birthdate="1994-01-01",
            onboarding_complete=True,
            is_active=True,
            is_verified=True
        )
        
        monitoring_service = PolicyMonitoringService(db)
        
        # Test policy change check
        check_result = await monitoring_service.check_for_policy_changes()
        
        # Test getting policy changes for user
        user_changes = await monitoring_service.get_policy_changes_for_user(mock_user, 30)
        
        # Test notification preferences
        preferences = await monitoring_service.get_user_notification_preferences(mock_user.id)
        
        # Test monitoring status
        status = {
            "monitoring_active": True,
            "last_check": monitoring_service.last_check.isoformat(),
            "monitoring_interval_hours": monitoring_service.monitoring_interval // 3600,
            "countries_monitored": len(await monitoring_service._get_active_countries())
        }
        
        return {
            "message": "Policy monitoring features tested successfully",
            "check_result": check_result,
            "user_changes": user_changes,
            "preferences": preferences,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error testing policy monitoring features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        ) 