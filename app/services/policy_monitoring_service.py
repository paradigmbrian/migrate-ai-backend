"""
Policy monitoring service for automated immigration policy change detection.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.policy import Policy
from app.models.country import Country
from app.models.user import User

logger = logging.getLogger(__name__)


class PolicyMonitoringService:
    """Service for monitoring immigration policy changes and managing notifications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.monitoring_interval = 24 * 60 * 60  # 24 hours in seconds
        self.last_check = datetime.utcnow()
    
    async def start_policy_monitoring(self):
        """Start the automated policy monitoring system."""
        logger.info("Starting automated policy monitoring system")
        
        async def monitoring_loop():
            while True:
                try:
                    await self.check_for_policy_changes()
                    await asyncio.sleep(self.monitoring_interval)
                except Exception as e:
                    logger.error(f"Error in policy monitoring loop: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
        
        # Start monitoring in background
        asyncio.create_task(monitoring_loop())
        logger.info("Policy monitoring system started")
    
    async def check_for_policy_changes(self) -> Dict[str, Any]:
        """
        Check for policy changes across all monitored countries.
        """
        try:
            logger.info("Checking for policy changes...")
            
            # Get all active countries
            countries = await self._get_active_countries()
            
            changes_detected = []
            
            for country in countries:
                country_changes = await self._check_country_policy_changes(country)
                if country_changes:
                    changes_detected.extend(country_changes)
            
            if changes_detected:
                logger.info(f"Detected {len(changes_detected)} policy changes")
                await self._process_policy_changes(changes_detected)
            else:
                logger.info("No policy changes detected")
            
            self.last_check = datetime.utcnow()
            
            return {
                'success': True,
                'changes_detected': len(changes_detected),
                'last_check': self.last_check
            }
            
        except Exception as e:
            logger.error(f"Error checking for policy changes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_policy_changes_for_user(
        self,
        user: User,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get policy changes relevant to a specific user.
        """
        try:
            # Get user's migration history and preferences
            user_countries = await self._get_user_relevant_countries(user.id)
            
            # Get recent policy changes for those countries
            recent_changes = await self._get_recent_policy_changes(
                user_countries, days_back
            )
            
            # Assess impact on user's migration plans
            impact_assessment = await self._assess_impact_on_user(
                user, recent_changes
            )
            
            return {
                'success': True,
                'policy_changes': recent_changes,
                'impact_assessment': impact_assessment,
                'relevant_countries': user_countries
            }
            
        except Exception as e:
            logger.error(f"Error getting policy changes for user: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_policy_change_notification(
        self,
        policy_change: Dict[str, Any],
        affected_users: List[User]
    ) -> Dict[str, Any]:
        """
        Create and send notifications for policy changes.
        """
        try:
            notifications_created = []
            
            for user in affected_users:
                # Check user's notification preferences
                user_preferences = await self._get_user_notification_preferences(user.id)
                
                if self._should_notify_user(user_preferences, policy_change):
                    notification = await self._create_user_notification(
                        user, policy_change, user_preferences
                    )
                    notifications_created.append(notification)
            
            logger.info(f"Created {len(notifications_created)} policy change notifications")
            
            return {
                'success': True,
                'notifications_created': len(notifications_created),
                'notifications': notifications_created
            }
            
        except Exception as e:
            logger.error(f"Error creating policy change notifications: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def assess_policy_change_impact(
        self,
        policy_change: Dict[str, Any],
        user_checklists: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess the impact of a policy change on user checklists.
        """
        try:
            impact_analysis = {
                'policy_change': policy_change,
                'affected_checklists': [],
                'timeline_impact': {},
                'requirement_changes': [],
                'recommendations': []
            }
            
            for checklist in user_checklists:
                checklist_impact = await self._assess_checklist_impact(
                    policy_change, checklist
                )
                
                if checklist_impact['is_affected']:
                    impact_analysis['affected_checklists'].append(checklist_impact)
            
            # Generate recommendations
            impact_analysis['recommendations'] = self._generate_impact_recommendations(
                impact_analysis
            )
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Error assessing policy change impact: {e}")
            return {
                'error': str(e),
                'affected_checklists': [],
                'recommendations': []
            }
    
    async def get_user_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's notification preferences for policy changes.
        """
        try:
            # This would typically query a user_preferences table
            # For now, return default preferences
            return {
                'policy_changes': True,
                'timeline_updates': True,
                'requirement_changes': True,
                'fee_changes': True,
                'notification_frequency': 'daily',
                'notification_method': 'email',
                'countries_of_interest': ['all'],
                'policy_types': ['visa', 'documentation', 'fees', 'timeline']
            }
        except Exception as e:
            logger.error(f"Error getting user notification preferences: {e}")
            return {
                'policy_changes': True,
                'notification_frequency': 'daily',
                'notification_method': 'email'
            }
    
    async def update_user_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user's notification preferences.
        """
        try:
            # This would typically update a user_preferences table
            # For now, just log the update
            logger.info(f"Updated notification preferences for user {user_id}: {preferences}")
            
            return {
                'success': True,
                'message': 'Notification preferences updated successfully',
                'preferences': preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating user notification preferences: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Private helper methods
    
    async def _get_active_countries(self) -> List[Country]:
        """Get all active countries for policy monitoring."""
        try:
            result = await self.db.execute(
                text("SELECT * FROM countries WHERE is_active = true")
            )
            return result.fetchall()
        except Exception as e:
            logger.error(f"Error getting active countries: {e}")
            return []
    
    async def _check_country_policy_changes(self, country: Country) -> List[Dict[str, Any]]:
        """Check for policy changes in a specific country."""
        try:
            # This would typically involve:
            # 1. Scraping official government websites
            # 2. Checking RSS feeds
            # 3. Monitoring API endpoints
            # 4. Comparing with stored policy data
            
            # For now, simulate policy change detection
            changes = []
            
            # Simulate checking different policy aspects
            visa_changes = await self._check_visa_policy_changes(country)
            if visa_changes:
                changes.extend(visa_changes)
            
            fee_changes = await self._check_fee_changes(country)
            if fee_changes:
                changes.extend(fee_changes)
            
            timeline_changes = await self._check_timeline_changes(country)
            if timeline_changes:
                changes.extend(timeline_changes)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error checking policy changes for {country.name}: {e}")
            return []
    
    async def _check_visa_policy_changes(self, country: Country) -> List[Dict[str, Any]]:
        """Check for visa policy changes."""
        # This would involve scraping official visa information
        # For now, return empty list (no changes detected)
        return []
    
    async def _check_fee_changes(self, country: Country) -> List[Dict[str, Any]]:
        """Check for fee changes."""
        # This would involve checking for fee updates
        # For now, return empty list (no changes detected)
        return []
    
    async def _check_timeline_changes(self, country: Country) -> List[Dict[str, Any]]:
        """Check for processing timeline changes."""
        # This would involve checking for timeline updates
        # For now, return empty list (no changes detected)
        return []
    
    async def _process_policy_changes(self, changes: List[Dict[str, Any]]):
        """Process detected policy changes."""
        try:
            for change in changes:
                # Store the policy change
                await self._store_policy_change(change)
                
                # Find affected users
                affected_users = await self._find_affected_users(change)
                
                # Create notifications
                if affected_users:
                    await self.create_policy_change_notification(change, affected_users)
                
                logger.info(f"Processed policy change: {change.get('title', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Error processing policy changes: {e}")
    
    async def _store_policy_change(self, change: Dict[str, Any]):
        """Store a policy change in the database."""
        try:
            # This would typically insert into a policy_changes table
            logger.info(f"Storing policy change: {change.get('title', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error storing policy change: {e}")
    
    async def _find_affected_users(self, change: Dict[str, Any]) -> List[User]:
        """Find users affected by a policy change."""
        try:
            # This would query users based on the policy change
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error finding affected users: {e}")
            return []
    
    async def _get_user_relevant_countries(self, user_id: str) -> List[str]:
        """Get countries relevant to a user based on their migration history."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT DISTINCT 
                        COALESCE(origin_country_id, '') as origin,
                        COALESCE(destination_country_id, '') as destination
                    FROM checklists 
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            
            countries = []
            for row in result.fetchall():
                if row.origin:
                    countries.append(row.origin)
                if row.destination:
                    countries.append(row.destination)
            
            return list(set(countries))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting user relevant countries: {e}")
            return []
    
    async def _get_recent_policy_changes(
        self,
        countries: List[str],
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Get recent policy changes for specific countries."""
        try:
            # This would query a policy_changes table
            # For now, return mock data
            return [
                {
                    'id': 'change-1',
                    'country_id': countries[0] if countries else 'usa',
                    'change_type': 'visa_requirements',
                    'title': 'Updated Visa Requirements',
                    'description': 'New documentation requirements for work visas',
                    'effective_date': (datetime.now() + timedelta(days=30)).isoformat(),
                    'impact_level': 'medium',
                    'details': {
                        'old_requirements': ['Passport', 'Job offer'],
                        'new_requirements': ['Passport', 'Job offer', 'Educational certificates', 'Language test results']
                    }
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent policy changes: {e}")
            return []
    
    async def _assess_impact_on_user(
        self,
        user: User,
        policy_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess the impact of policy changes on a specific user."""
        try:
            impact = {
                'user_id': user.id,
                'total_changes': len(policy_changes),
                'high_impact_changes': 0,
                'medium_impact_changes': 0,
                'low_impact_changes': 0,
                'affected_checklists': [],
                'recommendations': []
            }
            
            for change in policy_changes:
                if change.get('impact_level') == 'high':
                    impact['high_impact_changes'] += 1
                elif change.get('impact_level') == 'medium':
                    impact['medium_impact_changes'] += 1
                else:
                    impact['low_impact_changes'] += 1
            
            # Generate recommendations based on impact
            if impact['high_impact_changes'] > 0:
                impact['recommendations'].append(
                    "Review your migration timeline - significant policy changes detected"
                )
            
            if impact['medium_impact_changes'] > 0:
                impact['recommendations'].append(
                    "Check if any new requirements affect your current checklist"
                )
            
            return impact
            
        except Exception as e:
            logger.error(f"Error assessing impact on user: {e}")
            return {
                'user_id': user.id,
                'error': str(e)
            }
    
    def _should_notify_user(
        self,
        user_preferences: Dict[str, Any],
        policy_change: Dict[str, Any]
    ) -> bool:
        """Determine if a user should be notified about a policy change."""
        try:
            # Check if user wants policy change notifications
            if not user_preferences.get('policy_changes', True):
                return False
            
            # Check notification frequency
            last_notification = user_preferences.get('last_notification')
            if last_notification:
                last_notification_date = datetime.fromisoformat(last_notification)
                if user_preferences.get('notification_frequency') == 'daily':
                    if datetime.now() - last_notification_date < timedelta(days=1):
                        return False
                elif user_preferences.get('notification_frequency') == 'weekly':
                    if datetime.now() - last_notification_date < timedelta(weeks=1):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification preferences: {e}")
            return True  # Default to notify if there's an error
    
    async def _create_user_notification(
        self,
        user: User,
        policy_change: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a notification for a specific user."""
        try:
            notification = {
                'user_id': user.id,
                'policy_change_id': policy_change.get('id'),
                'title': f"Policy Change Alert: {policy_change.get('title', 'Unknown')}",
                'message': self._generate_notification_message(policy_change),
                'priority': policy_change.get('impact_level', 'medium'),
                'created_at': datetime.utcnow().isoformat(),
                'notification_method': user_preferences.get('notification_method', 'email'),
                'read': False
            }
            
            # This would typically store the notification in a database
            logger.info(f"Created notification for user {user.id}: {notification['title']}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating user notification: {e}")
            return {
                'error': str(e)
            }
    
    def _generate_notification_message(self, policy_change: Dict[str, Any]) -> str:
        """Generate a user-friendly notification message."""
        try:
            title = policy_change.get('title', 'Policy Change')
            description = policy_change.get('description', '')
            effective_date = policy_change.get('effective_date', '')
            impact_level = policy_change.get('impact_level', 'medium')
            
            message = f"""
Policy Change Alert: {title}

{description}

Impact Level: {impact_level.title()}
Effective Date: {effective_date}

Please review your migration checklist to ensure compliance with the new requirements.
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating notification message: {e}")
            return "A policy change has been detected. Please review your migration checklist."
    
    async def _assess_checklist_impact(
        self,
        policy_change: Dict[str, Any],
        checklist: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of a policy change on a specific checklist."""
        try:
            impact = {
                'checklist_id': checklist.get('id'),
                'is_affected': False,
                'affected_items': [],
                'timeline_impact': 'none',
                'requirement_changes': []
            }
            
            # Check if the policy change affects this checklist
            change_country = policy_change.get('country_id')
            checklist_origin = checklist.get('origin_country_id')
            checklist_destination = checklist.get('destination_country_id')
            
            if change_country in [checklist_origin, checklist_destination]:
                impact['is_affected'] = True
                
                # Analyze impact on checklist items
                for category in checklist.get('categories', []):
                    for item in category.get('items', []):
                        if self._item_affected_by_change(item, policy_change):
                            impact['affected_items'].append({
                                'item_title': item.get('title'),
                                'impact_description': f"Affected by {policy_change.get('change_type')} change"
                            })
            
            return impact
            
        except Exception as e:
            logger.error(f"Error assessing checklist impact: {e}")
            return {
                'checklist_id': checklist.get('id'),
                'is_affected': False,
                'error': str(e)
            }
    
    def _item_affected_by_change(
        self,
        item: Dict[str, Any],
        policy_change: Dict[str, Any]
    ) -> bool:
        """Check if a checklist item is affected by a policy change."""
        try:
            change_type = policy_change.get('change_type', '')
            item_title = item.get('title', '').lower()
            
            # Simple keyword matching - in production, this would be more sophisticated
            if 'visa' in change_type and 'visa' in item_title:
                return True
            elif 'document' in change_type and 'document' in item_title:
                return True
            elif 'fee' in change_type and 'fee' in item_title:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking item impact: {e}")
            return False
    
    def _generate_impact_recommendations(self, impact_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on impact analysis."""
        try:
            recommendations = []
            
            affected_count = len(impact_analysis.get('affected_checklists', []))
            
            if affected_count > 0:
                recommendations.append(
                    f"Review {affected_count} checklist(s) that may be affected by policy changes"
                )
                recommendations.append(
                    "Update your timeline to account for new requirements"
                )
                recommendations.append(
                    "Consider consulting with an immigration professional for guidance"
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating impact recommendations: {e}")
            return ["Review your migration plan for any policy changes"]


# Create singleton instance
policy_monitoring_service = PolicyMonitoringService(None)  # Will be initialized with db session 