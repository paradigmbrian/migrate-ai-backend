"""
Profile service for profile management operations.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.profile import ProfileUpdate

# Set up logging
logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_profile(self, user_id: str) -> Optional[User]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User object or None if not found
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> User:
        """
        Update user profile with provided data.
        
        Args:
            user_id: User's UUID
            updates: Dictionary of fields to update
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found
        """
        try:
            user = await self.get_user_profile(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'birthdate']
            for field, value in updates.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            # Update timestamp
            user.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Profile updated for user: {user_id}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user profile: {str(e)}")
            raise
    
    async def validate_profile_update(self, profile_update: ProfileUpdate) -> Dict[str, Any]:
        """
        Validate profile update data.
        
        Args:
            profile_update: ProfileUpdate object
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Pydantic validation is already handled by the schema
            # Additional business logic validation can be added here
            
            validation_result = {
                'valid': True,
                'error': None
            }
            
            # Check if at least one field is provided
            update_data = profile_update.model_dump(exclude_unset=True)
            if not update_data:
                validation_result['valid'] = False
                validation_result['error'] = "At least one field must be provided for update"
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating profile update: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    async def get_profile_completion_status(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate profile completion status.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dictionary with completion status information
        """
        try:
            user = await self.get_user_profile(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Define required fields for profile completion
            required_fields = {
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'email': 'Email',
                'birthdate': 'Birthdate'
            }
            
            completed_fields = []
            missing_fields = []
            
            # Check each required field
            for field, display_name in required_fields.items():
                value = getattr(user, field, None)
                if value and str(value).strip():
                    completed_fields.append(display_name)
                else:
                    missing_fields.append(display_name)
            
            # Calculate completion percentage
            total_fields = len(required_fields)
            completed_count = len(completed_fields)
            completion_percentage = int((completed_count / total_fields) * 100)
            
            # Determine if profile is complete
            is_complete = completion_percentage == 100
            
            # Generate suggestions for missing fields
            suggestions = []
            if 'First Name' in missing_fields:
                suggestions.append("Add your first name to complete your profile")
            if 'Last Name' in missing_fields:
                suggestions.append("Add your last name to complete your profile")
            if 'Birthdate' in missing_fields:
                suggestions.append("Add your birthdate to complete your profile")
            
            return {
                'completion_percentage': completion_percentage,
                'completed_fields': completed_fields,
                'missing_fields': missing_fields,
                'total_fields': total_fields,
                'is_complete': is_complete,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Error calculating profile completion status: {str(e)}")
            raise
    
    async def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user profile information.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dictionary with profile summary
        """
        try:
            user = await self.get_user_profile(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")
            
            # Get completion status
            completion_status = await self.get_profile_completion_status(user_id)
            
            return {
                'user_id': user.id,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'onboarding_complete': user.onboarding_complete,
                'last_login': user.last_login,
                'profile_completion': completion_status['completion_percentage'],
                'is_profile_complete': completion_status['is_complete']
            }
            
        except Exception as e:
            logger.error(f"Error getting profile summary: {str(e)}")
            raise 