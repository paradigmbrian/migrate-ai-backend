"""
Cognito authentication endpoints for user registration and login.
"""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserCreate
from app.schemas.user import UserResponse
from app.services.cognito_service import cognito_service
from app.services.profile_sync_service import ProfileSyncService
from app.services.cognito_user_status_service import CognitoUserStatusService
import uuid
from pydantic import BaseModel

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


class LogoutRequest(BaseModel):
    access_token: str

@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user from AWS Cognito and invalidate session.
    """
    logger.info("Logout attempt initiated")
    
    try:
        # Add timeout to prevent hanging
        import asyncio
        
        # Create a timeout wrapper for the Cognito call
        async def logout_with_timeout():
            try:
                logout_response = await cognito_service.sign_out(logout_data.access_token)
                return logout_response
            except Exception as e:
                logger.error(f"Cognito logout error: {e}")
                return {'success': False, 'error_message': str(e)}
        
        # Call with timeout
        try:
            logout_response = await asyncio.wait_for(logout_with_timeout(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warn("Cognito logout timed out, but continuing with local logout")
            logout_response = {'success': True, 'message': 'Logout completed (Cognito timeout)'}
        
        if not logout_response.get('success'):
            error_msg = logout_response.get('error_message', 'Logout failed')
            logger.error(f"Cognito logout failed: {error_msg}")
            # Don't raise exception, just log and continue
            logger.info("Continuing with local logout despite Cognito failure")
        
        logger.info("User successfully logged out")
        
        return {
            "message": "Successfully logged out",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Return success even if there's an error, to prevent hanging
        return {
            "message": "Logout completed (with errors)",
            "success": True
        }


@router.post("/user/activity")
async def update_user_activity(
    user_id: str,
    activity_type: str = "heartbeat",
    db: AsyncSession = Depends(get_db)
):
    """
    Update user activity and online status.
    """
    logger.info(f"User activity update: {user_id} - {activity_type}")
    
    try:
        status_service = CognitoUserStatusService(db)
        result = await status_service.update_user_activity(user_id, activity_type)
        
        if result['success']:
            return {
                "message": "Activity updated successfully",
                "user_id": user_id,
                "status": result['status'],
                "last_activity": result['last_activity']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update activity: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Activity update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update activity"
        )


@router.get("/user/{user_id}/status")
async def get_user_status(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user status and session information.
    """
    logger.info(f"Getting user status: {user_id}")
    
    try:
        status_service = CognitoUserStatusService(db)
        result = await status_service.get_user_status(user_id)
        
        if result['status'] == 'not_found':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        elif result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user status: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user status"
        )


@router.get("/user/{user_id}/session")
async def get_user_session_info(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed session information for a user.
    """
    logger.info(f"Getting user session info: {user_id}")
    
    try:
        status_service = CognitoUserStatusService(db)
        result = await status_service.get_user_session_info(user_id)
        
        if result['status'] == 'not_found':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        elif result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting session info: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session info"
        )


@router.post("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: str = Form(...),
    state: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    """
    logger.info(f"Google OAuth callback received with code: {code[:10]}...")
    
    try:
        # Get the redirect URI from the request
        redirect_uri = str(request.url_for('google_oauth_callback'))
        
        # Exchange authorization code for tokens
        oauth_result = await cognito_service.initiate_google_oauth(code, redirect_uri)
        
        if not oauth_result.get('success'):
            error_msg = oauth_result.get('error_message', 'OAuth flow failed')
            logger.error(f"Google OAuth failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth authentication failed: {error_msg}"
            )
        
        user_info = oauth_result['user_info']
        logger.info(f"Google OAuth successful for user: {user_info.get('email')}")
        
        # Check if user exists in our database
        sync_service = ProfileSyncService(db)
        
        # Prepare user data for sync
        cognito_user_data = {
            'sub': user_info.get('sub'),
            'email': user_info.get('email'),
            'given_name': user_info.get('given_name', ''),
            'family_name': user_info.get('family_name', ''),
        }
        
        try:
            user = await sync_service.sync_cognito_user_to_db(cognito_user_data)
            logger.info(f"User synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not authenticate user. User sync failed."
            )
        
        # Create session data
        session_data = {
            'access_token': oauth_result.get('access_token'),
            'id_token': oauth_result.get('id_token'),
            'refresh_token': oauth_result.get('refresh_token'),
            'expires_in': oauth_result.get('expires_in', 3600),
            'token_type': 'Bearer',
            'provider': 'google'
        }
        
        # Return success response with tokens
        return {
            'success': True,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            },
            'session': session_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OAuth authentication"
        )

@router.post("/google/login")
async def google_login(
    id_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with Google ID token.
    """
    logger.info("Google login attempt with ID token")
    
    try:
        # Validate the Google ID token
        validation_result = await cognito_service.validate_google_token(id_token)
        
        if not validation_result.get('success'):
            error_msg = validation_result.get('error_message', 'Token validation failed')
            logger.error(f"Google token validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {error_msg}"
            )
        
        user_info = validation_result['user_info']
        logger.info(f"Google token validated for user: {user_info.get('email')}")
        
        # Check if user exists in our database
        sync_service = ProfileSyncService(db)
        
        # Prepare user data for sync
        cognito_user_data = {
            'sub': user_info.get('sub'),
            'email': user_info.get('email'),
            'given_name': user_info.get('given_name', ''),
            'family_name': user_info.get('family_name', ''),
        }
        
        try:
            user = await sync_service.sync_cognito_user_to_db(cognito_user_data)
            logger.info(f"User synced to database: {user.id}")
        except Exception as sync_error:
            logger.error(f"Failed to sync user to database: {sync_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not authenticate user. User sync failed."
            )
        
        # Create session data (using the ID token as access token for now)
        session_data = {
            'access_token': id_token,  # Using ID token as access token
            'id_token': id_token,
            'expires_in': 3600,  # Default expiration
            'token_type': 'Bearer',
            'provider': 'google'
        }
        
        # Return success response
        return {
            'success': True,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            },
            'session': session_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Google authentication"
        )

@router.get("/google/auth-url")
async def get_google_auth_url():
    """
    Get Google OAuth authorization URL.
    """
    try:
        auth_url = await cognito_service.get_google_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error getting Google auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Google auth URL"
        ) 