"""
Profile synchronization service for Cognito and database integration.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.services.cognito_service import CognitoService


class ProfileSyncService:
    """Service for synchronizing user profiles between Cognito and database."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cognito_service = CognitoService()
    
    async def sync_cognito_user_to_db(self, cognito_user_data: Dict[str, Any]) -> User:
        """
        Sync Cognito user data to database.
        
        Args:
            cognito_user_data: User data from Cognito response
            
        Returns:
            User: The synced user object
            
        Raises:
            Exception: If sync fails
        """
        try:
            # Extract data from Cognito response
            cognito_sub = cognito_user_data.get('sub')
            email = cognito_user_data.get('email')
            first_name = cognito_user_data.get('given_name', '')
            last_name = cognito_user_data.get('family_name', '')
            birthdate = cognito_user_data.get('birthdate', '')
            
            if not cognito_sub or not email:
                raise ValueError("Missing required Cognito data: sub or email")
            
            # Try to find existing user by cognito_sub first
            user = await self.get_user_by_cognito_sub(cognito_sub)
            
            if user:
                # User exists - merge data and update last_login
                user = await self.merge_user_data(
                    cognito_data={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birthdate': birthdate,
                        'email': email
                    },
                    db_user=user
                )
                user.last_login = datetime.utcnow()
                await self.db.commit()
                return user
            else:
                # New user - create with onboarding_complete = True
                user = User(
                    id=str(uuid.uuid4()),
                    cognito_sub=cognito_sub,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    birthdate=birthdate,
                    onboarding_complete=True,  # User successfully registered
                    last_login=datetime.utcnow(),
                    is_active=True,
                    is_verified=True
                )
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                return user
                
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Failed to sync user data: {str(e)}")
    
    async def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        """
        Find user by Cognito sub.
        
        Args:
            cognito_sub: Cognito's unique user identifier
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.cognito_sub == cognito_sub)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email (fallback method).
        
        Args:
            email: User's email address
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def merge_user_data(self, cognito_data: Dict[str, Any], db_user: User) -> User:
        """
        Merge Cognito data with existing database user data.
        Uses simple strategy: prefer Cognito data for auth fields.
        
        Args:
            cognito_data: Data from Cognito
            db_user: Existing user from database
            
        Returns:
            User: Updated user object
        """
        # Update user data (prefer Cognito data for auth fields)
        if cognito_data.get('first_name'):
            db_user.first_name = cognito_data['first_name']
        if cognito_data.get('last_name'):
            db_user.last_name = cognito_data['last_name']
        if cognito_data.get('birthdate'):
            db_user.birthdate = cognito_data['birthdate']
        if cognito_data.get('email'):
            db_user.email = cognito_data['email']
        
        # Update timestamp
        db_user.updated_at = datetime.utcnow()
        
        return db_user
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> User:
        """
        Update user profile data.
        
        Args:
            user_id: User's UUID
            updates: Dictionary of fields to update
            
        Returns:
            User: Updated user object
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'birthdate', 'onboarding_complete']
        for field, value in updates.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_user_profile(self, user_id: str) -> Optional[User]:
        """
        Get complete user profile.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def handle_sync_conflicts(self, cognito_data: Dict[str, Any], db_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle conflicts between Cognito and database data.
        For now, uses simple strategy: prefer Cognito data for auth fields.
        
        Args:
            cognito_data: Data from Cognito
            db_data: Data from database
            
        Returns:
            Dict: Merged data
        """
        merged_data = db_data.copy()
        
        # Prefer Cognito data for auth-related fields
        auth_fields = ['first_name', 'last_name', 'birthdate', 'email']
        for field in auth_fields:
            if field in cognito_data and cognito_data[field]:
                merged_data[field] = cognito_data[field]
        
        return merged_data 