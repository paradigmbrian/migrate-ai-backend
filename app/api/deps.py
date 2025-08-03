"""
Dependencies for FastAPI endpoints.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.services.cognito_service import cognito_service

# Security scheme
security = HTTPBearer()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user using Cognito JWT validation."""
    try:
        # Verify JWT token with Cognito
        token_response = await cognito_service.verify_token(credentials.credentials)
        
        if not token_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user sub from token payload
        user_sub = token_response.get('user_sub')
        if not user_sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database using Cognito user sub
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_sub))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(db, credentials)
    except HTTPException:
        return None


async def get_cognito_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current Cognito user data."""
    try:
        # Verify token and get user data
        token_response = await cognito_service.verify_token(credentials.credentials)
        
        if not token_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get detailed user information from Cognito
        user_response = await cognito_service.get_user(credentials.credentials)
        
        if not user_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not get user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 