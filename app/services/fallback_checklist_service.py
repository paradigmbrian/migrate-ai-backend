"""
Fallback checklist service for when OpenAI is not available.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from app.models.user import User
from app.models.country import Country

logger = logging.getLogger(__name__)


class FallbackChecklistService:
    """Fallback service for generating checklists when AI is not available."""
    
    def __init__(self):
        """Initialize fallback service."""
        self.logger = logging.getLogger(__name__)
    
    def generate_checklist(
        self,
        user: User,
        origin_country: Country,
        destination_country: Country,
        reason_for_moving: str
    ) -> Dict[str, Any]:
        """
        Generate a fallback checklist using predefined templates.
        """
        try:
            self.logger.info(f"Generating fallback checklist for user {user.id}")
            
            # Create a basic checklist structure
            checklist = {
                "categories": [
                    {
                        "name": "Pre-Departure Preparation",
                        "description": "Essential tasks to complete before leaving your home country",
                        "items": [
                            {
                                "title": "Obtain valid passport",
                                "description": "Ensure your passport is valid for at least 6 months beyond your planned stay",
                                "priority": "High",
                                "estimated_days": 30,
                                "dependencies": [],
                                "tips": [
                                    "Apply early as passport processing can take several weeks",
                                    "Check if you need additional pages for visas"
                                ],
                                "country_specific": False,
                                "required_documents": ["Current passport", "Passport photos", "Application form"]
                            },
                            {
                                "title": "Research visa requirements",
                                "description": "Understand the specific visa requirements for your destination",
                                "priority": "High",
                                "estimated_days": 14,
                                "dependencies": [],
                                "tips": [
                                    "Visit the official government website of your destination country",
                                    "Consider consulting with an immigration lawyer"
                                ],
                                "country_specific": True,
                                "required_documents": ["Research notes", "Official requirements"]
                            },
                            {
                                "title": "Gather essential documents",
                                "description": "Collect all necessary documents for your visa application",
                                "priority": "High",
                                "estimated_days": 21,
                                "dependencies": ["Obtain valid passport"],
                                "tips": [
                                    "Make multiple copies of all documents",
                                    "Consider getting documents translated if required"
                                ],
                                "country_specific": True,
                                "required_documents": ["Birth certificate", "Marriage certificate", "Educational certificates", "Employment records"]
                            }
                        ]
                    },
                    {
                        "name": "Visa Application Process",
                        "description": "Steps to complete your visa application",
                        "items": [
                            {
                                "title": "Complete visa application form",
                                "description": "Fill out the required visa application form accurately",
                                "priority": "High",
                                "estimated_days": 7,
                                "dependencies": ["Research visa requirements"],
                                "tips": [
                                    "Double-check all information before submitting",
                                    "Keep a copy of your completed application"
                                ],
                                "country_specific": True,
                                "required_documents": ["Application form", "Supporting documents"]
                            },
                            {
                                "title": "Schedule visa appointment",
                                "description": "Book an appointment at the embassy or consulate",
                                "priority": "Medium",
                                "estimated_days": 14,
                                "dependencies": ["Complete visa application form"],
                                "tips": [
                                    "Book appointments well in advance",
                                    "Be prepared for potential delays"
                                ],
                                "country_specific": True,
                                "required_documents": ["Application confirmation", "Appointment confirmation"]
                            },
                            {
                                "title": "Attend visa interview",
                                "description": "Attend your scheduled visa interview",
                                "priority": "High",
                                "estimated_days": 1,
                                "dependencies": ["Schedule visa appointment"],
                                "tips": [
                                    "Dress professionally",
                                    "Bring all required documents",
                                    "Be honest and concise in your answers"
                                ],
                                "country_specific": True,
                                "required_documents": ["All application documents", "Interview confirmation"]
                            }
                        ]
                    },
                    {
                        "name": "Pre-Arrival Planning",
                        "description": "Tasks to complete before arriving in your destination country",
                        "items": [
                            {
                                "title": "Book accommodation",
                                "description": "Secure temporary or permanent accommodation",
                                "priority": "Medium",
                                "estimated_days": 14,
                                "dependencies": ["Attend visa interview"],
                                "tips": [
                                    "Research different neighborhoods",
                                    "Consider temporary accommodation initially"
                                ],
                                "country_specific": False,
                                "required_documents": ["Rental agreement", "Deposit payment"]
                            },
                            {
                                "title": "Arrange transportation",
                                "description": "Plan your travel to the destination country",
                                "priority": "Medium",
                                "estimated_days": 7,
                                "dependencies": ["Book accommodation"],
                                "tips": [
                                    "Book flights well in advance for better prices",
                                    "Consider arrival time and local transportation"
                                ],
                                "country_specific": False,
                                "required_documents": ["Flight tickets", "Travel insurance"]
                            },
                            {
                                "title": "Set up banking",
                                "description": "Open a bank account in your destination country",
                                "priority": "Medium",
                                "estimated_days": 21,
                                "dependencies": ["Attend visa interview"],
                                "tips": [
                                    "Research different banks and their requirements",
                                    "Consider online banking options"
                                ],
                                "country_specific": True,
                                "required_documents": ["Passport", "Visa", "Proof of address"]
                            }
                        ]
                    },
                    {
                        "name": "Post-Arrival Tasks",
                        "description": "Essential tasks to complete after arriving in your destination country",
                        "items": [
                            {
                                "title": "Register with local authorities",
                                "description": "Complete any required registration with local government",
                                "priority": "High",
                                "estimated_days": 7,
                                "dependencies": ["Attend visa interview"],
                                "tips": [
                                    "Check specific requirements for your visa type",
                                    "Keep copies of all registration documents"
                                ],
                                "country_specific": True,
                                "required_documents": ["Passport", "Visa", "Proof of address"]
                            },
                            {
                                "title": "Obtain local identification",
                                "description": "Get any required local identification documents",
                                "priority": "Medium",
                                "estimated_days": 14,
                                "dependencies": ["Register with local authorities"],
                                "tips": [
                                    "Research what ID documents are available to you",
                                    "Keep your passport safe as primary identification"
                                ],
                                "country_specific": True,
                                "required_documents": ["Passport", "Visa", "Registration documents"]
                            },
                            {
                                "title": "Find healthcare provider",
                                "description": "Register with a local healthcare provider",
                                "priority": "Medium",
                                "estimated_days": 14,
                                "dependencies": ["Obtain local identification"],
                                "tips": [
                                    "Research healthcare systems in your destination",
                                    "Consider private health insurance"
                                ],
                                "country_specific": True,
                                "required_documents": ["Local ID", "Health insurance information"]
                            }
                        ]
                    }
                ],
                "total_estimated_days": 120,
                "legal_disclaimer": "This checklist is for informational purposes only. Please consult with qualified immigration professionals and official government sources for accurate, up-to-date information. Requirements may vary based on individual circumstances and current regulations.",
                "personalized_notes": f"Generated fallback checklist for {user.first_name} {user.last_name} moving from {origin_country.name} to {destination_country.name}. This checklist provides general guidance and should be customized based on your specific circumstances and current requirements."
            }
            
            return {
                'success': True,
                'checklist': checklist,
                'generated_at': datetime.utcnow(),
                'model_used': 'fallback-template',
                'fallback_used': True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating fallback checklist: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    def get_personalized_recommendations(
        self,
        user: User,
        current_checklist_progress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get fallback personalized recommendations.
        """
        try:
            recommendations = {
                "priority_recommendations": [
                    "Start with high-priority tasks like passport and visa requirements",
                    "Keep all documents organized and make multiple copies",
                    "Research specific requirements for your destination country"
                ],
                "timing_suggestions": [
                    "Begin visa application process at least 3-6 months before planned departure",
                    "Book flights and accommodation 2-3 months in advance",
                    "Complete post-arrival tasks within the first month"
                ],
                "potential_challenges": [
                    "Processing times may be longer than expected",
                    "Requirements may change, so stay updated",
                    "Language barriers in some countries"
                ],
                "motivational_message": f"Keep going, {user.first_name}! Immigration is a journey, and every step you complete brings you closer to your goal. Stay organized and don't hesitate to seek help when needed.",
                "additional_resources": [
                    "Official government websites of your destination country",
                    "Local expat communities and forums",
                    "Professional immigration consultants"
                ],
                "next_steps": [
                    "Review your current progress and identify the next priority task",
                    "Set specific deadlines for upcoming tasks",
                    "Consider joining online communities for support and advice"
                ]
            }
            
            return {
                'success': True,
                'recommendations': recommendations,
                'generated_at': datetime.utcnow(),
                'fallback_used': True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating fallback recommendations: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    def get_smart_tips(
        self,
        user: User,
        current_task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get fallback smart tips for a specific task.
        """
        try:
            tips = {
                "tips": [
                    "Start early and allow extra time for unexpected delays",
                    "Keep detailed records of all applications and communications",
                    "Make multiple copies of important documents",
                    "Stay organized with a dedicated folder or digital system"
                ],
                "common_mistakes": [
                    "Missing deadlines or waiting too long to start",
                    "Incomplete or inaccurate application forms",
                    "Not keeping copies of submitted documents",
                    "Failing to research specific country requirements"
                ],
                "optimal_approach": "Take a systematic approach: research thoroughly, prepare all documents in advance, and maintain clear records of your progress.",
                "timing_advice": "Begin this task as soon as possible, as immigration processes often take longer than expected.",
                "legal_notes": "Always verify information with official sources and consider consulting with qualified immigration professionals for complex situations."
            }
            
            return {
                'success': True,
                'tips': tips,
                'generated_at': datetime.utcnow(),
                'fallback_used': True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating fallback tips: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }


# Create singleton instance
fallback_checklist_service = FallbackChecklistService() 