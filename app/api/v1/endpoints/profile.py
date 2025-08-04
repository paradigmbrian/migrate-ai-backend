"""
Profile management endpoints for user profile operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdate, ProfileStatus
from app.services.profile_service import ProfileService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information.
    """
    try:
        profile_service = ProfileService(db)
        profile = await profile_service.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return ProfileResponse.from_orm(profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve profile"
        )


@router.put("/profile", response_model=ProfileResponse)
async def update_user_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    """
    try:
        profile_service = ProfileService(db)
        
        # Validate the update data
        validation_result = await profile_service.validate_profile_update(profile_update)
        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result['error']
            )
        
        # Update the profile
        updated_profile = await profile_service.update_user_profile(
            current_user.id, 
            profile_update.model_dump(exclude_unset=True)
        )
        
        logger.info(f"Profile updated for user: {current_user.id}")
        return ProfileResponse.from_orm(updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile"
        )


@router.get("/profile/status", response_model=ProfileStatus)
async def get_profile_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile completion status.
    """
    try:
        profile_service = ProfileService(db)
        status_info = await profile_service.get_profile_completion_status(current_user.id)
        
        return ProfileStatus(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve profile status"
        ) 