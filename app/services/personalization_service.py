"""
Personalization service for enhanced user experience and dynamic content.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.user import User
from app.models.country import Country
from app.models.checklist import Checklist, ChecklistItem

logger = logging.getLogger(__name__)


class PersonalizationService:
    """Service for personalizing user experience and content."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_personalization_profile(self, user: User) -> Dict[str, Any]:
        """
        Get comprehensive personalization profile for a user.
        """
        try:
            # Calculate age from birthdate
            age = None
            if user.birthdate:
                try:
                    birth_date = datetime.strptime(user.birthdate, "%Y-%m-%d")
                    age = (datetime.now() - birth_date).days // 365
                except:
                    age = None
            
            # Get user's migration history
            migration_history = await self._get_user_migration_history(user.id)
            
            # Get user's checklist completion patterns
            completion_patterns = await self._get_completion_patterns(user.id)
            
            # Determine user experience level
            experience_level = self._determine_experience_level(migration_history, completion_patterns)
            
            # Get user preferences and patterns
            preferences = await self._get_user_preferences(user.id)
            
            return {
                'user_id': user.id,
                'age': age,
                'experience_level': experience_level,
                'migration_history': migration_history,
                'completion_patterns': completion_patterns,
                'preferences': preferences,
                'personalization_score': self._calculate_personalization_score(
                    age, experience_level, migration_history, completion_patterns
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting user personalization profile: {e}")
            return {
                'user_id': user.id,
                'experience_level': 'beginner',
                'personalization_score': 0.5
            }
    
    async def enhance_checklist_with_personalization(
        self,
        checklist: Dict[str, Any],
        user: User,
        origin_country: Country,
        destination_country: Country
    ) -> Dict[str, Any]:
        """
        Enhance a checklist with personalized content and suggestions.
        """
        try:
            # Get user personalization profile
            profile = await self.get_user_personalization_profile(user)
            
            # Enhance checklist based on user profile
            enhanced_checklist = checklist.copy()
            
            # Add personalized notes and suggestions
            enhanced_checklist['personalized_notes'] = self._generate_personalized_notes(
                profile, origin_country, destination_country
            )
            
            # Adjust task complexity based on experience level
            enhanced_checklist['categories'] = self._adjust_task_complexity(
                checklist['categories'], profile['experience_level']
            )
            
            # Add smart defaults and suggestions
            enhanced_checklist['smart_suggestions'] = self._generate_smart_suggestions(
                profile, origin_country, destination_country
            )
            
            # Add personalized timing recommendations
            enhanced_checklist['timing_recommendations'] = self._generate_timing_recommendations(
                profile, checklist
            )
            
            return enhanced_checklist
            
        except Exception as e:
            logger.error(f"Error enhancing checklist with personalization: {e}")
            return checklist
    
    async def get_dynamic_content_for_country_pair(
        self,
        origin_country: Country,
        destination_country: Country,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get dynamic content specific to a country pair and user profile.
        """
        try:
            # Get country-specific requirements
            requirements = await self._get_country_specific_requirements(
                origin_country, destination_country
            )
            
            # Get visa type recommendations
            visa_recommendations = self._get_visa_recommendations(
                origin_country, destination_country, user_profile
            )
            
            # Get cultural and practical tips
            cultural_tips = self._get_cultural_tips(destination_country, user_profile)
            
            # Get cost estimates
            cost_estimates = self._get_cost_estimates(
                origin_country, destination_country, user_profile
            )
            
            return {
                'requirements': requirements,
                'visa_recommendations': visa_recommendations,
                'cultural_tips': cultural_tips,
                'cost_estimates': cost_estimates,
                'country_pair_specific': True
            }
            
        except Exception as e:
            logger.error(f"Error getting dynamic content for country pair: {e}")
            return {
                'requirements': [],
                'visa_recommendations': [],
                'cultural_tips': [],
                'cost_estimates': {},
                'country_pair_specific': False
            }
    
    async def generate_smart_defaults(
        self,
        user: User,
        origin_country: Country,
        destination_country: Country
    ) -> Dict[str, Any]:
        """
        Generate smart defaults based on user profile and country pair.
        """
        try:
            profile = await self.get_user_personalization_profile(user)
            
            # Generate optimal timing suggestions
            timing_suggestions = self._generate_optimal_timing(
                profile, origin_country, destination_country
            )
            
            # Generate document suggestions
            document_suggestions = self._generate_document_suggestions(
                profile, origin_country, destination_country
            )
            
            # Generate budget suggestions
            budget_suggestions = self._generate_budget_suggestions(
                profile, origin_country, destination_country
            )
            
            return {
                'timing_suggestions': timing_suggestions,
                'document_suggestions': document_suggestions,
                'budget_suggestions': budget_suggestions,
                'priority_order': self._generate_priority_order(profile)
            }
            
        except Exception as e:
            logger.error(f"Error generating smart defaults: {e}")
            return {
                'timing_suggestions': [],
                'document_suggestions': [],
                'budget_suggestions': {},
                'priority_order': []
            }
    
    async def get_personalized_tips_and_advice(
        self,
        user: User,
        current_task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get personalized tips and advice based on user profile and current context.
        """
        try:
            profile = await self.get_user_personalization_profile(user)
            
            # Generate context-aware tips
            tips = self._generate_context_aware_tips(
                profile, current_task, context
            )
            
            # Generate motivational messages
            motivational_messages = self._generate_motivational_messages(profile)
            
            # Generate progress-specific advice
            progress_advice = self._generate_progress_advice(profile, context)
            
            return {
                'tips': tips,
                'motivational_messages': motivational_messages,
                'progress_advice': progress_advice,
                'personalized_for': user.first_name
            }
            
        except Exception as e:
            logger.error(f"Error getting personalized tips: {e}")
            return {
                'tips': ["Stay organized and keep track of your progress"],
                'motivational_messages': ["You're doing great! Keep going!"],
                'progress_advice': ["Continue with your current tasks"],
                'personalized_for': user.first_name
            }
    
    # Private helper methods
    
    async def _get_user_migration_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's migration history from checklists."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT c.*, co.name as origin_name, cd.name as destination_name
                    FROM checklists c
                    LEFT JOIN countries co ON c.origin_country_id = co.id
                    LEFT JOIN countries cd ON c.destination_country_id = cd.id
                    WHERE c.user_id = :user_id
                    ORDER BY c.created_at DESC
                """),
                {"user_id": user_id}
            )
            
            checklists = result.fetchall()
            return [
                {
                    'id': c.id,
                    'origin_country': c.origin_name,
                    'destination_country': c.destination_name,
                    'created_at': c.created_at,
                    'completed_at': c.completed_at,
                    'is_completed': c.is_completed
                }
                for c in checklists
            ]
        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            return []
    
    async def _get_completion_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get user's checklist completion patterns."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_checklists,
                        COUNT(CASE WHEN is_completed = true THEN 1 END) as completed_checklists,
                        AVG(CASE WHEN is_completed = true 
                            THEN EXTRACT(EPOCH FROM (completed_at - created_at))/86400 
                            ELSE NULL END) as avg_completion_days
                    FROM checklists 
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            
            row = result.fetchone()
            return {
                'total_checklists': row.total_checklists or 0,
                'completed_checklists': row.completed_checklists or 0,
                'completion_rate': (row.completed_checklists / row.total_checklists * 100) if row.total_checklists > 0 else 0,
                'avg_completion_days': row.avg_completion_days or 0
            }
        except Exception as e:
            logger.error(f"Error getting completion patterns: {e}")
            return {
                'total_checklists': 0,
                'completed_checklists': 0,
                'completion_rate': 0,
                'avg_completion_days': 0
            }
    
    def _determine_experience_level(
        self,
        migration_history: List[Dict[str, Any]],
        completion_patterns: Dict[str, Any]
    ) -> str:
        """Determine user's experience level based on history and patterns."""
        if completion_patterns['total_checklists'] == 0:
            return 'beginner'
        elif completion_patterns['total_checklists'] >= 3 and completion_patterns['completion_rate'] >= 80:
            return 'expert'
        elif completion_patterns['total_checklists'] >= 1 and completion_patterns['completion_rate'] >= 60:
            return 'intermediate'
        else:
            return 'beginner'
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and patterns."""
        # This would typically come from user settings or behavior analysis
        # For now, return default preferences
        return {
            'preferred_complexity': 'medium',
            'notification_preferences': 'email',
            'language_preference': 'en',
            'timezone': 'UTC'
        }
    
    def _calculate_personalization_score(
        self,
        age: Optional[int],
        experience_level: str,
        migration_history: List[Dict[str, Any]],
        completion_patterns: Dict[str, Any]
    ) -> float:
        """Calculate a personalization score for the user."""
        score = 0.5  # Base score
        
        # Age factor
        if age and 25 <= age <= 45:
            score += 0.1  # Prime migration age
        
        # Experience factor
        if experience_level == 'expert':
            score += 0.2
        elif experience_level == 'intermediate':
            score += 0.1
        
        # History factor
        if len(migration_history) > 0:
            score += 0.1
        
        # Completion factor
        if completion_patterns['completion_rate'] > 70:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_personalized_notes(
        self,
        profile: Dict[str, Any],
        origin_country: Country,
        destination_country: Country
    ) -> str:
        """Generate personalized notes based on user profile."""
        notes = []
        
        if profile['experience_level'] == 'beginner':
            notes.append("As a first-time migrant, we recommend starting early and allowing extra time for each step.")
        elif profile['experience_level'] == 'expert':
            notes.append("With your experience, you can optimize the process by focusing on country-specific requirements.")
        
        if profile['age'] and profile['age'] > 40:
            notes.append("Consider additional health and insurance requirements for your age group.")
        
        return " ".join(notes)
    
    def _adjust_task_complexity(
        self,
        categories: List[Dict[str, Any]],
        experience_level: str
    ) -> List[Dict[str, Any]]:
        """Adjust task complexity based on user experience level."""
        adjusted_categories = []
        
        for category in categories:
            adjusted_category = category.copy()
            adjusted_items = []
            
            for item in category['items']:
                adjusted_item = item.copy()
                
                if experience_level == 'beginner':
                    # Add more detailed descriptions for beginners
                    if 'description' in adjusted_item:
                        adjusted_item['description'] += " (This step is crucial for beginners - take your time to ensure accuracy)"
                    # Add more tips
                    if 'tips' in adjusted_item:
                        adjusted_item['tips'].extend([
                            "Don't hesitate to ask for help if you're unsure",
                            "Double-check all information before submitting"
                        ])
                elif experience_level == 'expert':
                    # Streamline for experts
                    if 'tips' in adjusted_item:
                        adjusted_item['tips'] = [tip for tip in adjusted_item['tips'] if 'advanced' in tip.lower() or 'optimization' in tip.lower()]
                
                adjusted_items.append(adjusted_item)
            
            adjusted_category['items'] = adjusted_items
            adjusted_categories.append(adjusted_category)
        
        return adjusted_categories
    
    def _generate_smart_suggestions(
        self,
        profile: Dict[str, Any],
        origin_country: Country,
        destination_country: Country
    ) -> List[str]:
        """Generate smart suggestions based on user profile."""
        suggestions = []
        
        if profile['experience_level'] == 'beginner':
            suggestions.append("Consider hiring an immigration consultant for your first migration")
            suggestions.append("Start the process at least 6 months before your planned departure")
        
        if profile['age'] and profile['age'] > 50:
            suggestions.append("Research retirement visa options if applicable")
        
        suggestions.append(f"Check for any special agreements between {origin_country.name} and {destination_country.name}")
        
        return suggestions
    
    def _generate_timing_recommendations(
        self,
        profile: Dict[str, Any],
        checklist: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized timing recommendations."""
        base_timeline = checklist.get('total_estimated_days', 180)
        
        if profile['experience_level'] == 'expert':
            timeline_multiplier = 0.8  # Experts can do it faster
        elif profile['experience_level'] == 'beginner':
            timeline_multiplier = 1.3  # Beginners need more time
        else:
            timeline_multiplier = 1.0
        
        adjusted_timeline = int(base_timeline * timeline_multiplier)
        
        return {
            'recommended_start_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'estimated_completion_date': (datetime.now() + timedelta(days=adjusted_timeline)).strftime('%Y-%m-%d'),
            'critical_milestones': [
                {'task': 'Visa Application', 'days_from_start': adjusted_timeline // 3},
                {'task': 'Document Preparation', 'days_from_start': adjusted_timeline // 6},
                {'task': 'Final Preparations', 'days_from_start': adjusted_timeline - 30}
            ]
        }
    
    async def _get_country_specific_requirements(
        self,
        origin_country: Country,
        destination_country: Country
    ) -> List[Dict[str, Any]]:
        """Get country-specific requirements for the country pair."""
        # This would typically query a database of country-specific requirements
        # For now, return some common requirements
        return [
            {
                'requirement': 'Visa Type',
                'description': f'Check specific visa requirements for {origin_country.name} to {destination_country.name}',
                'priority': 'High'
            },
            {
                'requirement': 'Language Requirements',
                'description': f'Verify language requirements for {destination_country.name}',
                'priority': 'Medium'
            },
            {
                'requirement': 'Health Requirements',
                'description': f'Check health screening requirements for {destination_country.name}',
                'priority': 'Medium'
            }
        ]
    
    def _get_visa_recommendations(
        self,
        origin_country: Country,
        destination_country: Country,
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get visa recommendations based on country pair and user profile."""
        recommendations = []
        
        # Basic visa types
        visa_types = destination_country.visa_types.split(', ') if destination_country.visa_types else []
        
        for visa_type in visa_types:
            recommendation = {
                'visa_type': visa_type.strip(),
                'description': f'{visa_type} visa for {destination_country.name}',
                'suitability': 'Good' if 'Work' in visa_type else 'Check requirements'
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_cultural_tips(self, destination_country: Country, user_profile: Dict[str, Any]) -> List[str]:
        """Get cultural tips for the destination country."""
        tips = [
            f"Research cultural norms and customs in {destination_country.name}",
            "Learn basic phrases in the local language",
            "Understand local business etiquette",
            "Research local transportation and housing options"
        ]
        
        return tips
    
    def _get_cost_estimates(
        self,
        origin_country: Country,
        destination_country: Country,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get cost estimates for the migration."""
        base_visa_cost = destination_country.application_fee_usd or 100
        
        return {
            'visa_application_fee': base_visa_cost,
            'estimated_total_cost': base_visa_cost * 3,  # Including other expenses
            'cost_breakdown': {
                'visa_fees': base_visa_cost,
                'document_preparation': base_visa_cost * 0.5,
                'travel_expenses': base_visa_cost * 1.5
            }
        }
    
    def _generate_optimal_timing(
        self,
        profile: Dict[str, Any],
        origin_country: Country,
        destination_country: Country
    ) -> List[Dict[str, Any]]:
        """Generate optimal timing suggestions."""
        suggestions = []
        
        if profile['experience_level'] == 'beginner':
            suggestions.append({
                'phase': 'Preparation',
                'timing': '6-12 months before departure',
                'reason': 'Allow extra time for first-time migrants'
            })
        else:
            suggestions.append({
                'phase': 'Preparation',
                'timing': '3-6 months before departure',
                'reason': 'Experienced migrants can optimize timing'
            })
        
        suggestions.append({
            'phase': 'Visa Application',
            'timing': f'{destination_country.processing_time_days + 30} days before departure',
            'reason': f'Account for {destination_country.processing_time_days} days processing time plus buffer'
        })
        
        return suggestions
    
    def _generate_document_suggestions(
        self,
        profile: Dict[str, Any],
        origin_country: Country,
        destination_country: Country
    ) -> List[str]:
        """Generate document suggestions."""
        suggestions = [
            "Valid passport with at least 6 months validity",
            "Birth certificate",
            "Educational certificates",
            "Employment records",
            "Financial statements"
        ]
        
        if profile['age'] and profile['age'] > 50:
            suggestions.append("Health insurance documentation")
            suggestions.append("Retirement planning documents")
        
        return suggestions
    
    def _generate_budget_suggestions(
        self,
        profile: Dict[str, Any],
        origin_country: Country,
        destination_country: Country
    ) -> Dict[str, Any]:
        """Generate budget suggestions."""
        base_cost = destination_country.application_fee_usd or 100
        
        return {
            'minimum_budget': base_cost * 2,
            'recommended_budget': base_cost * 4,
            'budget_categories': {
                'visa_fees': base_cost,
                'document_preparation': base_cost * 0.5,
                'travel_expenses': base_cost * 1.5,
                'emergency_fund': base_cost * 1.0
            }
        }
    
    def _generate_priority_order(self, profile: Dict[str, Any]) -> List[str]:
        """Generate priority order for tasks."""
        if profile['experience_level'] == 'beginner':
            return [
                "Research visa requirements",
                "Gather essential documents",
                "Apply for visa",
                "Book travel arrangements",
                "Final preparations"
            ]
        else:
            return [
                "Apply for visa",
                "Gather documents",
                "Book travel",
                "Final preparations"
            ]
    
    def _generate_context_aware_tips(
        self,
        profile: Dict[str, Any],
        current_task: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate context-aware tips."""
        tips = []
        
        if profile['experience_level'] == 'beginner':
            tips.append("Take your time with this task - accuracy is more important than speed")
            tips.append("Don't hesitate to seek help from official sources")
        
        if 'visa' in current_task.lower():
            tips.append("Double-check all information before submitting your visa application")
            tips.append("Keep copies of all submitted documents")
        
        if 'interview' in current_task.lower():
            tips.append("Practice common interview questions")
            tips.append("Prepare to explain your reasons for migration clearly")
        
        return tips
    
    def _generate_motivational_messages(self, profile: Dict[str, Any]) -> List[str]:
        """Generate motivational messages."""
        messages = [
            "You're making great progress on your migration journey!",
            "Every step you complete brings you closer to your goal",
            "Stay organized and keep moving forward"
        ]
        
        if profile['experience_level'] == 'beginner':
            messages.append("Remember, everyone starts somewhere - you're doing great!")
        elif profile['experience_level'] == 'expert':
            messages.append("Your experience is your advantage - use it wisely!")
        
        return messages
    
    def _generate_progress_advice(
        self,
        profile: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate progress-specific advice."""
        advice = []
        
        progress_percentage = context.get('progress_percentage', 0)
        
        if progress_percentage < 25:
            advice.append("You're just getting started - focus on understanding the requirements")
        elif progress_percentage < 50:
            advice.append("You're making good progress - keep up the momentum")
        elif progress_percentage < 75:
            advice.append("You're in the home stretch - stay focused on the remaining tasks")
        else:
            advice.append("Almost there! Double-check everything before final submission")
        
        return advice 