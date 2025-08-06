"""
Cognito user status service for real-time user status updates.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.cognito_service import cognito_service

logger = logging.getLogger(__name__)


class CognitoUserStatusService:
    """Service for managing Cognito user status and real-time updates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_users: Dict[str, Dict[str, Any]] = {}
        self._status_check_interval = 60  # seconds
    
    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get current user status from Cognito and database."""
        try:
            # Get user from database
            result = await self.db.execute(
                text("SELECT * FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            user = result.fetchone()
            
            if not user:
                return {
                    'status': 'not_found',
                    'last_seen': None,
                    'is_online': False,
                    'cognito_status': 'unknown'
                }
            
            # Get Cognito user status if we have a cognito_sub
            cognito_status = 'unknown'
            if user.cognito_sub:
                try:
                    cognito_user = await cognito_service.get_user_by_sub(user.cognito_sub)
                    if cognito_user.get('success'):
                        cognito_status = cognito_user.get('user_status', 'unknown')
                except Exception as e:
                    logger.warning(f"Failed to get Cognito status for user {user_id}: {e}")
            
            # Check if user is in active users list
            is_online = user_id in self._active_users
            
            return {
                'status': 'active' if is_online else 'inactive',
                'last_seen': self._active_users.get(user_id, {}).get('last_seen'),
                'is_online': is_online,
                'cognito_status': cognito_status,
                'user_id': user_id,
                'email': user.email
            }
            
        except Exception as e:
            logger.error(f"Error getting user status for {user_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def update_user_activity(self, user_id: str, activity_type: str = 'heartbeat') -> Dict[str, Any]:
        """Update user activity and online status."""
        try:
            now = datetime.utcnow()
            
            # Update active users list
            self._active_users[user_id] = {
                'last_seen': now,
                'activity_type': activity_type,
                'is_online': True
            }
            
            # Update database with last activity
            await self.db.execute(
                text("""
                    UPDATE users 
                    SET last_activity = :last_activity,
                        updated_at = NOW()
                    WHERE id = :user_id
                """),
                {
                    'last_activity': now,
                    'user_id': user_id
                }
            )
            
            await self.db.commit()
            
            return {
                'success': True,
                'user_id': user_id,
                'last_activity': now,
                'status': 'online'
            }
            
        except Exception as e:
            logger.error(f"Error updating user activity for {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def mark_user_offline(self, user_id: str) -> Dict[str, Any]:
        """Mark user as offline."""
        try:
            # Remove from active users
            if user_id in self._active_users:
                del self._active_users[user_id]
            
            # Update database
            await self.db.execute(
                text("""
                    UPDATE users 
                    SET last_activity = :last_activity,
                        updated_at = NOW()
                    WHERE id = :user_id
                """),
                {
                    'last_activity': datetime.utcnow(),
                    'user_id': user_id
                }
            )
            
            await self.db.commit()
            
            return {
                'success': True,
                'user_id': user_id,
                'status': 'offline'
            }
            
        except Exception as e:
            logger.error(f"Error marking user offline for {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_online_users(self) -> List[Dict[str, Any]]:
        """Get list of currently online users."""
        try:
            online_users = []
            now = datetime.utcnow()
            
            # Filter out users who haven't been active in the last 5 minutes
            cutoff_time = now - timedelta(minutes=5)
            
            for user_id, user_data in self._active_users.items():
                if user_data['last_seen'] > cutoff_time:
                    online_users.append({
                        'user_id': user_id,
                        'last_seen': user_data['last_seen'],
                        'activity_type': user_data['activity_type']
                    })
                else:
                    # Remove stale entries
                    del self._active_users[user_id]
            
            return online_users
            
        except Exception as e:
            logger.error(f"Error getting online users: {e}")
            return []
    
    async def start_status_monitoring(self):
        """Start background task to monitor user status."""
        async def monitor_loop():
            while True:
                try:
                    # Clean up stale user entries
                    now = datetime.utcnow()
                    cutoff_time = now - timedelta(minutes=5)
                    
                    stale_users = [
                        user_id for user_id, user_data in self._active_users.items()
                        if user_data['last_seen'] < cutoff_time
                    ]
                    
                    for user_id in stale_users:
                        await self.mark_user_offline(user_id)
                    
                    if stale_users:
                        logger.info(f"Cleaned up {len(stale_users)} stale user entries")
                    
                    # Wait for next check
                    await asyncio.sleep(self._status_check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in status monitoring loop: {e}")
                    await asyncio.sleep(self._status_check_interval)
        
        # Start monitoring in background
        asyncio.create_task(monitor_loop())
        logger.info("Started Cognito user status monitoring")
    
    async def get_user_session_info(self, user_id: str) -> Dict[str, Any]:
        """Get detailed session information for a user."""
        try:
            # Get user from database
            result = await self.db.execute(
                text("""
                    SELECT u.*, 
                           COUNT(c.id) as checklist_count,
                           COUNT(CASE WHEN c.is_completed = true THEN 1 END) as completed_checklists
                    FROM users u
                    LEFT JOIN checklists c ON u.id = c.user_id
                    WHERE u.id = :user_id
                    GROUP BY u.id
                """),
                {"user_id": user_id}
            )
            user = result.fetchone()
            
            if not user:
                return {
                    'status': 'not_found',
                    'session_info': None
                }
            
            # Get current status
            status = await self.get_user_status(user_id)
            
            return {
                'status': 'found',
                'session_info': {
                    'user_id': user.id,
                    'email': user.email,
                    'is_online': status['is_online'],
                    'last_activity': user.last_activity,
                    'checklist_count': user.checklist_count or 0,
                    'completed_checklists': user.completed_checklists or 0,
                    'cognito_status': status['cognito_status'],
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting session info for {user_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            } 