"""
AWS Cognito service for authentication and user management.
"""

import boto3
import jwt
import os
import logging
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class CognitoService:
    """AWS Cognito service for user authentication and management."""
    
    def __init__(self):
        """Initialize Cognito client."""
        self._client = None
        self._user_pool_id = None
        self._client_id = None
    
    @property
    def client(self):
        """Lazy initialization of Cognito client."""
        if self._client is None:
            # Get configuration from environment or settings
            region = os.getenv('AWS_REGION') or settings.aws_region
            access_key = os.getenv('AWS_ACCESS_KEY_ID') or settings.aws_access_key_id
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or settings.aws_secret_access_key
            
            if not access_key or not secret_key:
                raise ValueError("AWS credentials not configured")
            
            self._client = boto3.client(
                'cognito-idp',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        return self._client
    
    @property
    def user_pool_id(self):
        """Get User Pool ID from environment or settings."""
        if self._user_pool_id is None:
            self._user_pool_id = os.getenv('COGNITO_USER_POOL_ID') or settings.cognito_user_pool_id
            if not self._user_pool_id:
                raise ValueError("COGNITO_USER_POOL_ID not configured")
        return self._user_pool_id
    
    @property
    def client_id(self):
        """Get Client ID from environment or settings."""
        if self._client_id is None:
            self._client_id = os.getenv('COGNITO_CLIENT_ID') or settings.cognito_client_id
            if not self._client_id:
                raise ValueError("COGNITO_CLIENT_ID not configured")
        return self._client_id
    
    async def sign_up(self, email: str, password: str, user_attributes: Dict[str, str]) -> Dict[str, Any]:
        """
        Sign up a new user with Cognito.
        
        Args:
            email: User's email address
            password: User's password
            user_attributes: Dictionary of user attributes
            
        Returns:
            Dictionary containing sign up response
        """
        logger.info(f"Starting Cognito sign up for email: {email}")
        logger.info(f"User attributes received: {user_attributes}")
        
        try:
            # Convert user attributes to Cognito format
            cognito_attributes = []
            for key, value in user_attributes.items():
                if key == 'email':
                    cognito_attributes.append({'Name': 'email', 'Value': value})
                elif key == 'given_name':
                    cognito_attributes.append({'Name': 'given_name', 'Value': value})
                elif key == 'family_name':
                    cognito_attributes.append({'Name': 'family_name', 'Value': value})
                elif key == 'birthdate':
                    cognito_attributes.append({'Name': 'birthdate', 'Value': value})
                elif key == 'custom:age':
                    cognito_attributes.append({'Name': 'custom:age', 'Value': str(value)})
                elif key == 'custom:marital_status':
                    cognito_attributes.append({'Name': 'custom:marital_status', 'Value': value})
                elif key == 'custom:profession':
                    cognito_attributes.append({'Name': 'custom:profession', 'Value': value})
                elif key == 'custom:dependents':
                    cognito_attributes.append({'Name': 'custom:dependents', 'Value': str(value)})
            
            logger.info(f"Converted Cognito attributes: {cognito_attributes}")
            logger.info(f"Using Client ID: {self.client_id}")
            
            # cognito_attributes ready for API call
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=cognito_attributes
            )
            
            logger.info(f"Cognito sign up successful, response: {response}")
            
            return {
                'success': True,
                'user_sub': response.get('UserSub'),
                'user_confirmed': response.get('UserConfirmed', False)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Cognito ClientError: {error_code} - {error_message}")
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }
        except Exception as e:
            logger.error(f"Unexpected error in Cognito sign up: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error_code': 'UNKNOWN_ERROR',
                'error_message': str(e)
            }
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user with Cognito.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing authentication tokens
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            authentication_result = response.get('AuthenticationResult', {})
            
            return {
                'success': True,
                'access_token': authentication_result.get('AccessToken'),
                'refresh_token': authentication_result.get('RefreshToken'),
                'id_token': authentication_result.get('IdToken'),
                'expires_in': authentication_result.get('ExpiresIn', 3600)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dictionary containing new access token
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            authentication_result = response.get('AuthenticationResult', {})
            
            return {
                'success': True,
                'access_token': authentication_result.get('AccessToken'),
                'id_token': authentication_result.get('IdToken'),
                'expires_in': authentication_result.get('ExpiresIn', 3600)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using an access token.
        
        Args:
            access_token: The access token
            
        Returns:
            Dictionary containing user information
        """
        try:
            response = self.client.get_user(
                AccessToken=access_token
            )
            
            user_attributes = {}
            for attr in response.get('UserAttributes', []):
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'success': True,
                'user_sub': response.get('Username'),
                'attributes': user_attributes
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token from Cognito.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Dictionary containing token payload if valid
        """
        try:
            # Decode token without verification first to get the header
            unverified_header = jwt.get_unverified_header(token)
            
            # Get the key ID from the header
            kid = unverified_header.get('kid')
            if not kid:
                return {'success': False, 'error': 'No key ID in token'}
            
            # Get the public keys from Cognito
            keys_url = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            
            # For now, we'll use a simplified approach
            # In production, you should fetch and cache the public keys
            payload = jwt.decode(
                token,
                options={"verify_signature": False}  # We'll implement proper verification later
            )
            
            return {
                'success': True,
                'payload': payload,
                'user_sub': payload.get('sub')
            }
            
        except jwt.InvalidTokenError as e:
            return {
                'success': False,
                'error': f'Invalid token: {str(e)}'
            }
    
    async def forgot_password(self, email: str) -> Dict[str, Any]:
        """
        Initiate forgot password flow.
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary containing response
        """
        try:
            response = self.client.forgot_password(
                ClientId=self.client_id,
                Username=email
            )
            
            return {
                'success': True,
                'delivery_medium': response.get('CodeDeliveryDetails', {}).get('DeliveryMedium')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }
    
    async def confirm_forgot_password(self, email: str, confirmation_code: str, new_password: str) -> Dict[str, Any]:
        """
        Confirm forgot password with confirmation code.
        
        Args:
            email: User's email address
            confirmation_code: Confirmation code sent to email
            new_password: New password
            
        Returns:
            Dictionary containing response
        """
        try:
            response = self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            
            return {'success': True}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }

    async def confirm_sign_up(self, username: str) -> Dict[str, Any]:
        """Confirm user sign up using admin_confirm_sign_up."""
        try:
            response = self.client.admin_confirm_sign_up(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            return {
                'success': True,
                'message': 'User confirmed successfully'
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
                                    # Log error for debugging
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }

    async def admin_sign_in(self, username: str, password: str) -> Dict[str, Any]:
        """Sign in user using admin_initiate_auth (bypasses user confirmation)."""
        try:
            response = self.client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            return {
                'success': True,
                'access_token': response['AuthenticationResult']['AccessToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
                                    # Log error for debugging
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message
            }


# Global instance
cognito_service = CognitoService() 