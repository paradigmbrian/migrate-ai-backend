"""
Cognito authentication endpoints for user registration and login.
"""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin
from app.schemas.user import UserResponse
from app.services.cognito_service import cognito_service
from app.services.profile_sync_service import ProfileSyncService
import uuid

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user using AWS Cognito.
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    try:
        # Prepare user attributes for Cognito
        user_attributes = {
            'email': user_data.email,
            'given_name': user_data.first_name,
            'family_name': user_data.last_name,
            'birthdate': user_data.birthdate or '1990-01-01',  # Required by User Pool
        }
        
        logger.info(f"Prepared Cognito attributes: {user_attributes}")
        
        # Register user with Cognito
        logger.info("Attempting Cognito sign up...")
        cognito_response = await cognito_service.sign_up(
            user_data.email,
            user_data.password,
            user_attributes
        )
        
        logger.info(f"Cognito sign up response: {cognito_response}")
        
        if not cognito_response.get('success'):
            error_msg = cognito_response.get('error_message', 'Registration failed')
            logger.error(f"Cognito registration failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {error_msg}"
            )
        
        logger.info("Cognito registration successful, syncing user to database")
        
        # Sync user to database using ProfileSyncService
        sync_service = ProfileSyncService(db)
        
        # Get user data from Cognito for sync
        cognito_user_data = {
            'sub': cognito_response['user_sub'],
            'email': user_data.email,
            'given_name': user_data.first_name,
            'family_name': user_data.last_name,
            'birthdate': user_data.birthdate or '1990-01-01',
        }
        
        try:
            user = await sync_service.sync_cognito_user_to_db(cognito_user_data)
            logger.info(f"User synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not log user in. User out of sync"
            )
        
        # Sign in the user immediately after registration
        logger.info("Attempting to sign in user after registration...")
        
        # First, try to confirm the user if they're not confirmed
        try:
            confirm_response = await cognito_service.confirm_sign_up(user_data.email)
            logger.info(f"User confirmation response: {confirm_response}")
        except Exception as confirm_error:
            logger.warning(f"User confirmation failed (user might already be confirmed): {confirm_error}")
        
        # Try regular sign-in first
        sign_in_response = await cognito_service.sign_in(user_data.email, user_data.password)
        
        logger.info(f"Sign in response: {sign_in_response}")
        
        if not sign_in_response.get('success'):
            # If regular sign-in fails, try admin sign-in (bypasses confirmation)
            logger.info("Regular sign-in failed, trying admin sign-in...")
            admin_sign_in_response = await cognito_service.admin_sign_in(user_data.email, user_data.password)
            
            if admin_sign_in_response.get('success'):
                logger.info("Admin sign-in successful")
                sign_in_response = admin_sign_in_response
            else:
                # Both sign-in methods failed
                logger.warning("Both regular and admin sign-in failed")
                return {
                    "access_token": "",
                    "token_type": "bearer",
                    "user": UserResponse.from_orm(user),
                    "message": "User registered successfully. Please sign in."
                }
        
        logger.info("Registration and sign-in successful")
        return {
            "access_token": sign_in_response['access_token'],
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        logger.error("HTTPException raised during registration")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not log user in. User out of sync"
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user using AWS Cognito and return access token.
    """
    try:
        # Sign in with Cognito
        sign_in_response = await cognito_service.sign_in(user_data.email, user_data.password)
        
        if not sign_in_response.get('success'):
            error_msg = sign_in_response.get('error_message', 'Invalid credentials')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {error_msg}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user data from Cognito for sync
        user_response = await cognito_service.get_user(sign_in_response['access_token'])
        
        if not user_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Sync user to database using ProfileSyncService
        sync_service = ProfileSyncService(db)
        
        # Prepare user data for sync
        cognito_user_data = {
            'sub': user_response['user_sub'],
            'email': user_response['attributes'].get('email', ''),
            'given_name': user_response['attributes'].get('given_name', ''),
            'family_name': user_response['attributes'].get('family_name', ''),
            'birthdate': user_response['attributes'].get('birthdate', '1990-01-01'),
        }
        
        try:
            user = await sync_service.sync_cognito_user_to_db(cognito_user_data)
            logger.info(f"User synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not log user in. User out of sync"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return {
            "access_token": sign_in_response['access_token'],
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not log user in. User out of sync"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        # Refresh token with Cognito
        refresh_response = await cognito_service.refresh_token(refresh_token)
        
        if not refresh_response.get('success'):
            error_msg = refresh_response.get('error_message', 'Token refresh failed')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {error_msg}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from the new access token
        user_response = await cognito_service.get_user(refresh_response['access_token'])
        
        if not user_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Sync user to database using ProfileSyncService
        sync_service = ProfileSyncService(db)
        
        # Prepare user data for sync
        cognito_user_data = {
            'sub': user_response['user_sub'],
            'email': user_response['attributes'].get('email', ''),
            'given_name': user_response['attributes'].get('given_name', ''),
            'family_name': user_response['attributes'].get('family_name', ''),
            'birthdate': user_response['attributes'].get('birthdate', '1990-01-01'),
        }
        
        try:
            user = await sync_service.sync_cognito_user_to_db(cognito_user_data)
            logger.info(f"User synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not log user in. User out of sync"
            )
        
        return {
            "access_token": refresh_response['access_token'],
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not log user in. User out of sync"
        )


@router.post("/forgot-password")
async def forgot_password(email: str):
    """
    Initiate forgot password flow.
    """
    try:
        response = await cognito_service.forgot_password(email)
        
        if not response.get('success'):
            error_msg = response.get('error_message', 'Password reset failed')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password reset failed: {error_msg}"
            )
        
        return {
            "message": "Password reset email sent",
            "delivery_medium": response.get('delivery_medium', 'EMAIL')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/confirm-forgot-password")
async def confirm_forgot_password(
    email: str,
    confirmation_code: str,
    new_password: str
):
    """
    Confirm forgot password with confirmation code.
    """
    try:
        response = await cognito_service.confirm_forgot_password(
            email,
            confirmation_code,
            new_password
        )
        
        if not response.get('success'):
            error_msg = response.get('error_message', 'Password confirmation failed')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password confirmation failed: {error_msg}"
            )
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password confirmation failed: {str(e)}"
        )


@router.post("/demo-login", response_model=Token)
async def demo_login(
    db: AsyncSession = Depends(get_db)
):
    """
    Demo login for development/testing purposes using Cognito.
    """
    try:
        demo_email = "demo@migrateai.com"
        demo_password = "DemoPassword123!"
        
        # Sign in the demo user
        sign_in_response = await cognito_service.sign_in(demo_email, demo_password)
        
        if not sign_in_response.get('success'):
            # If user is not confirmed, try to confirm them first
            if sign_in_response.get('error_code') == 'UserNotConfirmedException':
                # User not confirmed, attempting to confirm
                confirm_response = await cognito_service.confirm_sign_up(demo_email)
                if confirm_response.get('success'):
                    # Try sign in again after confirmation
                    sign_in_response = await cognito_service.sign_in(demo_email, demo_password)
                else:
                    # Failed to confirm user - continue to admin sign in
                    pass
            
            # If still failing, try admin sign in as fallback
            if not sign_in_response.get('success'):
                # Trying admin sign in as fallback
                sign_in_response = await cognito_service.admin_sign_in(demo_email, demo_password)
        
        if not sign_in_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo login failed"
            )
        
        # Get user data from Cognito for sync
        user_response = await cognito_service.get_user(sign_in_response['access_token'])
        
        if not user_response.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Sync user to database using ProfileSyncService
        sync_service = ProfileSyncService(db)
        
        try:
            user = await sync_service.sync_cognito_user_to_db(user_response['user_data'])
            logger.info(f"Demo user synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync demo user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not log user in. User out of sync"
            )
        
        return {
            "access_token": sign_in_response['access_token'],
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not log user in. User out of sync"
        ) 