"""
User migration service for moving existing demo users to AWS Cognito.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.user import User
from app.services.cognito_service import cognito_service
from app.services.profile_sync_service import ProfileSyncService

logger = logging.getLogger(__name__)


class UserMigrationService:
    """Service for migrating existing users to AWS Cognito."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sync_service = ProfileSyncService(db)
    
    async def get_existing_demo_users(self) -> List[Dict[str, Any]]:
        """Get all existing demo users from the database."""
        try:
            result = await self.db.execute(
                text("SELECT * FROM users WHERE email LIKE '%@migrate.ai'")
            )
            users = result.fetchall()
            
            return [
                {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'age': user.age,
                    'marital_status': user.marital_status,
                    'profession': user.profession,
                    'dependents': user.dependents,
                    'origin_country_code': user.origin_country_code,
                    'destination_country_code': user.destination_country_code,
                    'reason_for_moving': user.reason_for_moving,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                }
                for user in users
            ]
        except Exception as e:
            logger.error(f"Error fetching demo users: {e}")
            return []
    
    async def migrate_user_to_cognito(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate a single user to AWS Cognito."""
        try:
            # Prepare user attributes for Cognito
            user_attributes = {
                'email': user_data['email'],
                'given_name': user_data['first_name'],
                'family_name': user_data['last_name'],
                'birthdate': f"{2024 - user_data['age']}-01-01",  # Approximate birthdate
            }
            
            # Generate a default password for the user
            default_password = "MigrateAI2024!"
            
            # Register user with Cognito
            cognito_response = await cognito_service.sign_up(
                user_data['email'],
                default_password,
                user_attributes
            )
            
            if not cognito_response.get('success'):
                return {
                    'success': False,
                    'user_id': user_data['id'],
                    'email': user_data['email'],
                    'error': cognito_response.get('error_message', 'Unknown error')
                }
            
            # Confirm the user in Cognito
            confirm_response = await cognito_service.confirm_sign_up(user_data['email'])
            
            if not confirm_response.get('success'):
                logger.warning(f"Failed to confirm user {user_data['email']}: {confirm_response.get('error_message')}")
            
            # Sync user data to database with Cognito sub
            cognito_user_data = {
                'sub': cognito_response['user_sub'],
                'email': user_data['email'],
                'given_name': user_data['first_name'],
                'family_name': user_data['last_name'],
                'birthdate': f"{2024 - user_data['age']}-01-01",
            }
            
            # Update existing user record with Cognito sub
            await self.db.execute(
                text("""
                    UPDATE users 
                    SET cognito_sub = :cognito_sub, 
                        updated_at = NOW()
                    WHERE id = :user_id
                """),
                {
                    'cognito_sub': cognito_response['user_sub'],
                    'user_id': user_data['id']
                }
            )
            
            await self.db.commit()
            
            return {
                'success': True,
                'user_id': user_data['id'],
                'email': user_data['email'],
                'cognito_sub': cognito_response['user_sub'],
                'message': f"User {user_data['email']} migrated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error migrating user {user_data['email']}: {e}")
            return {
                'success': False,
                'user_id': user_data['id'],
                'email': user_data['email'],
                'error': str(e)
            }
    
    async def migrate_all_demo_users(self) -> Dict[str, Any]:
        """Migrate all existing demo users to AWS Cognito."""
        try:
            logger.info("Starting demo user migration to Cognito...")
            
            # Get existing demo users
            demo_users = await self.get_existing_demo_users()
            
            if not demo_users:
                return {
                    'success': True,
                    'message': 'No demo users found to migrate',
                    'migrated_count': 0,
                    'failed_count': 0,
                    'results': []
                }
            
            logger.info(f"Found {len(demo_users)} demo users to migrate")
            
            # Migrate each user
            results = []
            migrated_count = 0
            failed_count = 0
            
            for user_data in demo_users:
                result = await self.migrate_user_to_cognito(user_data)
                results.append(result)
                
                if result['success']:
                    migrated_count += 1
                    logger.info(f"✅ Migrated user: {user_data['email']}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to migrate user: {user_data['email']} - {result['error']}")
            
            return {
                'success': True,
                'message': f'Migration completed. {migrated_count} users migrated, {failed_count} failed',
                'migrated_count': migrated_count,
                'failed_count': failed_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            return {
                'success': False,
                'error': str(e),
                'migrated_count': 0,
                'failed_count': 0,
                'results': []
            } 