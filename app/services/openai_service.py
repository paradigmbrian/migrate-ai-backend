"""
OpenAI service for AI-powered checklist generation and recommendations.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from app.core.config import settings
from app.models.user import User
from app.models.country import Country
from app.services.fallback_checklist_service import fallback_checklist_service

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration and AI-powered features."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=30.0
        )
        self.model = "gpt-4-turbo-preview"  # Use latest GPT-4 model
    
    async def generate_checklist(
        self,
        user: User,
        origin_country: Country,
        destination_country: Country,
        reason_for_moving: str
    ) -> Dict[str, Any]:
        """
        Generate personalized checklist using OpenAI.
        
        Args:
            user: User profile information
            origin_country: Origin country details
            destination_country: Destination country details
            reason_for_moving: Reason for migration
            
        Returns:
            Dictionary containing generated checklist
        """
        # Check if OpenAI is configured
        if not self.client.api_key:
            logger.warning("OpenAI API key not configured, using fallback service")
            return fallback_checklist_service.generate_checklist(
                user, origin_country, destination_country, reason_for_moving
            )
        
        try:
            # Create context-aware prompt
            prompt = self._create_checklist_prompt(
                user, origin_country, destination_country, reason_for_moving
            )
            
            logger.info(f"Generating checklist for user {user.id}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert immigration consultant with deep knowledge of international migration processes. Generate comprehensive, accurate, and personalized checklists for people moving between countries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Parse the response
            checklist_data = self._parse_checklist_response(response.choices[0].message.content)
            
            return {
                'success': True,
                'checklist': checklist_data,
                'generated_at': datetime.utcnow(),
                'model_used': self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating checklist with OpenAI: {e}")
            logger.info("Falling back to static checklist service")
            return fallback_checklist_service.generate_checklist(
                user, origin_country, destination_country, reason_for_moving
            )
    
    async def get_personalized_recommendations(
        self,
        user: User,
        current_checklist_progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get AI-powered personalized recommendations.
        
        Args:
            user: User profile information
            current_checklist_progress: Current checklist progress
            
        Returns:
            Dictionary containing personalized recommendations
        """
        # Check if OpenAI is configured
        if not self.client.api_key:
            logger.warning("OpenAI API key not configured, using fallback service")
            return fallback_checklist_service.get_personalized_recommendations(
                user, current_checklist_progress
            )
        
        try:
            prompt = self._create_recommendations_prompt(user, current_checklist_progress)
            
            logger.info(f"Generating recommendations for user {user.id}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert immigration consultant. Provide personalized, actionable advice and recommendations based on the user's profile and current progress."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=1500,
                top_p=0.9
            )
            
            recommendations = self._parse_recommendations_response(response.choices[0].message.content)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations with OpenAI: {e}")
            logger.info("Falling back to static recommendations service")
            return fallback_checklist_service.get_personalized_recommendations(
                user, current_checklist_progress
            )
    
    async def get_smart_tips(
        self,
        user: User,
        current_task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get smart tips for a specific task.
        
        Args:
            user: User profile information
            current_task: Current task being worked on
            context: Additional context about the task
            
        Returns:
            Dictionary containing smart tips
        """
        # Check if OpenAI is configured
        if not self.client.api_key:
            logger.warning("OpenAI API key not configured, using fallback service")
            return fallback_checklist_service.get_smart_tips(
                user, current_task, context
            )
        
        try:
            prompt = self._create_tips_prompt(user, current_task, context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert immigration consultant. Provide specific, practical tips and advice for immigration tasks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=800,
                top_p=0.9
            )
            
            tips = self._parse_tips_response(response.choices[0].message.content)
            
            return {
                'success': True,
                'tips': tips,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating tips with OpenAI: {e}")
            logger.info("Falling back to static tips service")
            return fallback_checklist_service.get_smart_tips(
                user, current_task, context
            )
    
    def _create_checklist_prompt(
        self,
        user: User,
        origin_country: Country,
        destination_country: Country,
        reason_for_moving: str
    ) -> str:
        """Create a context-aware prompt for checklist generation."""
        
        # Calculate age from birthdate if available
        age = "Unknown"
        if user.birthdate:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(user.birthdate, "%Y-%m-%d")
                age = str((datetime.now() - birth_date).days // 365)
            except:
                age = "Unknown"
        
        prompt = f"""
Generate a comprehensive immigration checklist for the following scenario:

**User Profile:**
- Name: {user.first_name} {user.last_name}
- Age: {age} years old
- Email: {user.email}
- Origin Country: {origin_country.name} ({origin_country.code})
- Destination Country: {destination_country.name} ({destination_country.code})
- Reason for Moving: {reason_for_moving}

**Country Information:**
- Origin: {origin_country.name} - {origin_country.region}, GDP per capita: ${origin_country.gdp_per_capita:,.0f}
- Destination: {destination_country.name} - {destination_country.region}, GDP per capita: ${destination_country.gdp_per_capita:,.0f}
- Visa Types Available: {destination_country.visa_types}
- Processing Time: {destination_country.processing_time_days} days
- Application Fee: ${destination_country.application_fee_usd}

**Requirements:**
1. Generate a structured checklist with categories (Pre-Departure, Application Process, Post-Arrival, etc.)
2. Include specific requirements based on the user's profile and circumstances
3. Provide estimated timelines for each task
4. Include priority levels (High, Medium, Low)
5. Add country-specific requirements and tips
6. Consider the user's situation and the specific country pair
7. Include legal disclaimers and important notes

**Output Format:**
Return a JSON object with the following structure:
{{
    "categories": [
        {{
            "name": "Category Name",
            "description": "Category description",
            "items": [
                {{
                    "title": "Task title",
                    "description": "Detailed description",
                    "priority": "High|Medium|Low",
                    "estimated_days": 30,
                    "dependencies": ["task_id"],
                    "tips": ["tip1", "tip2"],
                    "country_specific": true,
                    "required_documents": ["doc1", "doc2"]
                }}
            ]
        }}
    ],
    "total_estimated_days": 180,
    "legal_disclaimer": "Important legal information",
    "personalized_notes": "Specific advice for this user"
}}
"""
        return prompt
    
    def _create_recommendations_prompt(
        self,
        user: User,
        current_progress: Dict[str, Any]
    ) -> str:
        """Create a prompt for personalized recommendations."""
        
        # Calculate age from birthdate if available
        age = "Unknown"
        if user.birthdate:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(user.birthdate, "%Y-%m-%d")
                age = str((datetime.now() - birth_date).days // 365)
            except:
                age = "Unknown"
        
        prompt = f"""
Based on the following user profile and current progress, provide personalized recommendations:

**User Profile:**
- Name: {user.first_name} {user.last_name}
- Age: {age}
- Email: {user.email}

**Current Progress:**
- Completed Tasks: {current_progress.get('completed_count', 0)}
- Total Tasks: {current_progress.get('total_count', 0)}
- Progress Percentage: {current_progress.get('progress_percentage', 0)}%
- Current Category: {current_progress.get('current_category', 'Unknown')}
- Next Priority Tasks: {current_progress.get('next_tasks', [])}

**Requirements:**
1. Analyze the user's progress and provide specific recommendations
2. Suggest optimal timing for remaining tasks
3. Identify potential bottlenecks or challenges
4. Provide motivation and encouragement
5. Suggest additional resources or tools
6. Consider the user's personal circumstances

**Output Format:**
Return a JSON object with:
{{
    "priority_recommendations": ["rec1", "rec2"],
    "timing_suggestions": ["timing1", "timing2"],
    "potential_challenges": ["challenge1", "challenge2"],
    "motivational_message": "Encouraging message",
    "additional_resources": ["resource1", "resource2"],
    "next_steps": ["step1", "step2"]
}}
"""
        return prompt
    
    def _create_tips_prompt(
        self,
        user: User,
        current_task: str,
        context: Dict[str, Any]
    ) -> str:
        """Create a prompt for smart tips."""
        
        prompt = f"""
Provide specific tips and advice for the following immigration task:

**User Context:**
- Name: {user.first_name} {user.last_name}
- Email: {user.email}

**Current Task:**
{current_task}

**Additional Context:**
{context}

**Requirements:**
1. Provide 3-5 specific, actionable tips
2. Include common mistakes to avoid
3. Suggest optimal timing or approach
4. Consider the user's specific circumstances
5. Include any relevant legal or procedural notes

**Output Format:**
Return a JSON object with:
{{
    "tips": ["tip1", "tip2", "tip3"],
    "common_mistakes": ["mistake1", "mistake2"],
    "optimal_approach": "Best approach description",
    "timing_advice": "When to do this task",
    "legal_notes": "Important legal information"
}}
"""
        return prompt
    
    def _parse_checklist_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the checklist response from OpenAI."""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: create a basic structure
                return {
                    "categories": [],
                    "total_estimated_days": 0,
                    "legal_disclaimer": "Please consult with a qualified immigration professional.",
                    "personalized_notes": "AI-generated checklist. Please verify all requirements."
                }
        except Exception as e:
            logger.error(f"Error parsing checklist response: {e}")
            return {
                "categories": [],
                "total_estimated_days": 0,
                "legal_disclaimer": "Error parsing response. Please consult with a qualified immigration professional.",
                "personalized_notes": "Unable to generate personalized checklist."
            }
    
    def _parse_recommendations_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the recommendations response from OpenAI."""
        try:
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "priority_recommendations": ["Continue with your current progress"],
                    "timing_suggestions": ["Follow the timeline in your checklist"],
                    "potential_challenges": ["Stay organized and keep track of deadlines"],
                    "motivational_message": "You're making great progress on your immigration journey!",
                    "additional_resources": ["Consult official government websites"],
                    "next_steps": ["Complete your current tasks"]
                }
        except Exception as e:
            logger.error(f"Error parsing recommendations response: {e}")
            return {
                "priority_recommendations": ["Continue with your checklist"],
                "timing_suggestions": ["Follow your timeline"],
                "potential_challenges": ["Stay organized"],
                "motivational_message": "Keep up the good work!",
                "additional_resources": ["Check official sources"],
                "next_steps": ["Complete current tasks"]
            }
    
    def _parse_tips_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the tips response from OpenAI."""
        try:
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "tips": ["Follow official guidelines", "Keep organized records"],
                    "common_mistakes": ["Missing deadlines", "Incomplete documentation"],
                    "optimal_approach": "Start early and stay organized",
                    "timing_advice": "Begin as soon as possible",
                    "legal_notes": "Consult with qualified professionals"
                }
        except Exception as e:
            logger.error(f"Error parsing tips response: {e}")
            return {
                "tips": ["Follow official guidelines"],
                "common_mistakes": ["Missing deadlines"],
                "optimal_approach": "Start early",
                "timing_advice": "Begin soon",
                "legal_notes": "Consult professionals"
            }


# Create singleton instance
openai_service = OpenAIService() 