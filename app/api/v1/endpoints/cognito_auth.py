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
    logger.info(f"User data received: {user_data.dict()}")
    
    try:
        # Check if user already exists in database
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        logger.info("No existing user found, proceeding with registration")
        
        # Prepare user attributes for Cognito
        user_attributes = {
            'email': user_data.email,
            'given_name': user_data.first_name,
            'family_name': user_data.last_name,
            'birthdate': '1990-01-01',  # Required by User Pool
        }
        
        logger.info(f"Prepared Cognito attributes: {user_attributes}")
        
        # Note: Custom attributes are not included to avoid configuration issues
        # User profile data will be stored in our database instead
        
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
        
        logger.info("Cognito registration successful, creating user in database")
        
        # Create user profile in our database
        new_user = User(
            id=cognito_response['user_sub'],  # Use Cognito user sub as ID
            email=user_data.email,
            hashed_password="",  # Password is managed by Cognito
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            age=user_data.age,
            marital_status=user_data.marital_status,
            profession=user_data.profession,
            dependents=user_data.dependents,
            origin_country_code=user_data.origin_country_code,
            destination_country_code=user_data.destination_country_code,
            reason_for_moving=user_data.reason_for_moving,
        )
        
        logger.info(f"Creating user in database with ID: {new_user.id}")
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info("User successfully created in database")
        
        # Sign in the user immediately after registration
        logger.info("Attempting to sign in user after registration...")
        sign_in_response = await cognito_service.sign_in(user_data.email, user_data.password)
        
        logger.info(f"Sign in response: {sign_in_response}")
        
        if not sign_in_response.get('success'):
            # Registration succeeded but sign-in failed
            logger.warning("Registration succeeded but sign-in failed")
            return {
                "access_token": "",
                "token_type": "bearer",
                "user": UserResponse.from_orm(new_user),
                "message": "User registered successfully. Please sign in."
            }
        
        logger.info("Registration and sign-in successful")
        return {
            "access_token": sign_in_response['access_token'],
            "token_type": "bearer",
            "user": UserResponse.from_orm(new_user)
        }
        
    except HTTPException:
        logger.error("HTTPException raised during registration")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
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
        
        # Get user from database
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == user_data.email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
                headers={"WWW-Authenticate": "Bearer"},
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
            detail=f"Login failed: {str(e)}"
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
        
        # Get user from database
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user_response['user_sub']))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
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
            detail=f"Token refresh failed: {str(e)}"
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
        
        # Check if demo user exists in database
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == demo_email))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create demo user in Cognito and database
            # Use only standard attributes for now
            user_attributes = {
                'email': demo_email,
                'given_name': 'Demo',
                'family_name': 'User',
                'birthdate': '1990-01-01',  # Required by User Pool
            }
            
            # Register with Cognito
            cognito_response = await cognito_service.sign_up(
                demo_email,
                demo_password,
                user_attributes
            )
            
            if not cognito_response.get('success'):
                # Try to sign in if user already exists
                sign_in_response = await cognito_service.sign_in(demo_email, demo_password)
                if not sign_in_response.get('success'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to create or sign in demo user"
                    )
                # Get the user_sub from the sign-in response or from Cognito
                # For now, we'll create a user with a generated UUID
                user_sub = str(uuid.uuid4())
            else:
                user_sub = cognito_response['user_sub']
            
            # Create user in database
            user = User(
                id=user_sub,
                email=demo_email,
                hashed_password="",
                first_name="Demo",
                last_name="User",
                age=30,
                marital_status="single",
                profession="Software Engineer",
                dependents=0,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
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
        
        # If user was not created in this request, fetch it from database
        if not user:
            result = await db.execute(select(User).where(User.email == demo_email))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Demo user not found in database"
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
            detail=f"Demo login failed: {str(e)}"
        ) 