"""
AI-powered checklist generation endpoints.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.models.country import Country
from app.services.openai_service import openai_service
from app.api.deps import get_current_user
from app.schemas.checklist import ChecklistCreate, ChecklistResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_ai_checklist(
    checklist_data: ChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI-powered personalized checklist.
    """
    logger.info(f"Generating AI checklist for user {current_user.id}")
    
    try:
        # Get origin and destination countries
        origin_country = await db.get(Country, checklist_data.origin_country_id)
        destination_country = await db.get(Country, checklist_data.destination_country_id)
        
        if not origin_country or not destination_country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Origin or destination country not found"
            )
        
        # Generate checklist using OpenAI
        result = await openai_service.generate_checklist(
            user=current_user,
            origin_country=origin_country,
            destination_country=destination_country,
            reason_for_moving=checklist_data.reason_for_moving
        )
        
        if not result['success']:
            logger.error(f"Failed to generate checklist: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate checklist: {result['error']}"
            )
        
        return {
            "message": "Checklist generated successfully",
            "checklist": result['checklist'],
            "generated_at": result['generated_at'],
            "model_used": result['model_used']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI checklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate checklist"
        )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered personalized recommendations based on user progress.
    """
    logger.info(f"Getting recommendations for user {current_user.id}")
    
    try:
        # Get current checklist progress
        # This would typically come from the user's current checklist
        # For now, we'll use a placeholder
        current_progress = {
            'completed_count': 0,
            'total_count': 0,
            'progress_percentage': 0,
            'current_category': 'Getting Started',
            'next_tasks': []
        }
        
        # Get recommendations from OpenAI
        result = await openai_service.get_personalized_recommendations(
            user=current_user,
            current_checklist_progress=current_progress
        )
        
        if not result['success']:
            logger.error(f"Failed to get recommendations: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get recommendations: {result['error']}"
            )
        
        return {
            "message": "Recommendations generated successfully",
            "recommendations": result['recommendations'],
            "generated_at": result['generated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.post("/tips", response_model=Dict[str, Any])
async def get_smart_tips(
    task: str,
    context: Dict[str, Any] = {},
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered smart tips for a specific task.
    """
    logger.info(f"Getting tips for user {current_user.id} on task: {task}")
    
    try:
        # Get tips from OpenAI
        result = await openai_service.get_smart_tips(
            user=current_user,
            current_task=task,
            context=context
        )
        
        if not result['success']:
            logger.error(f"Failed to get tips: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tips: {result['error']}"
            )
        
        return {
            "message": "Tips generated successfully",
            "tips": result['tips'],
            "generated_at": result['generated_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tips: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tips"
        )


@router.get("/health", response_model=Dict[str, Any])
async def check_ai_service_health():
    """
    Check if the AI service is available and configured.
    """
    try:
        # Check if OpenAI API key is configured
        if not openai_service.client.api_key:
            return {
                "status": "unconfigured",
                "message": "OpenAI API key not configured",
                "available": False
            }
        
        return {
            "status": "healthy",
            "message": "AI service is available",
            "available": True,
            "model": openai_service.model
        }
        
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"AI service error: {str(e)}",
            "available": False
        }


@router.post("/test-generate", response_model=Dict[str, Any])
async def test_generate_checklist():
    """
    Test endpoint to generate a sample checklist without authentication.
    This is for testing purposes only.
    """
    logger.info("Testing AI checklist generation")
    
    try:
        # Create a mock user and countries for testing
        from app.models.user import User
        from app.models.country import Country
        
        # Mock user data - using only the fields that exist in the User model
        mock_user = User(
            id="test-user-123",
            cognito_sub="test-cognito-sub",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            birthdate="1994-01-01",  # This gives us age ~30
            onboarding_complete=True,
            is_active=True,
            is_verified=True
        )
        
        # Mock countries
        mock_origin = Country(
            id="usa",
            code="USA",
            name="United States",
            flag_emoji="🇺🇸",
            region="North America",
            gdp_per_capita=69287.5,
            visa_types="Tourist, Business, Student, Work, Family",
            processing_time_days=30,
            application_fee_usd=160
        )
        
        mock_destination = Country(
            id="can",
            code="CAN", 
            name="Canada",
            flag_emoji="🇨🇦",
            region="North America",
            gdp_per_capita=51988.0,
            visa_types="Tourist, Business, Student, Work, Express Entry",
            processing_time_days=45,
            application_fee_usd=100
        )
        
        # Generate checklist using OpenAI service
        result = await openai_service.generate_checklist(
            user=mock_user,
            origin_country=mock_origin,
            destination_country=mock_destination,
            reason_for_moving="Career opportunity"
        )
        
        if result['success']:
            return {
                "message": "Test checklist generated successfully",
                "checklist": result['checklist'],
                "generated_at": result['generated_at'],
                "model_used": result.get('model_used', 'unknown'),
                "fallback_used": result.get('fallback_used', False)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate test checklist: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(f"Error in test checklist generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.post("/test-recommendations", response_model=Dict[str, Any])
async def test_get_recommendations():
    """
    Test endpoint to get personalized recommendations without authentication.
    This is for testing purposes only.
    """
    logger.info("Testing AI recommendations generation")
    
    try:
        # Create a mock user for testing
        from app.models.user import User
        
        # Mock user data
        mock_user = User(
            id="test-user-123",
            cognito_sub="test-cognito-sub",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            birthdate="1994-01-01",
            onboarding_complete=True,
            is_active=True,
            is_verified=True
        )
        
        # Mock current progress
        current_progress = {
            'completed_count': 3,
            'total_count': 10,
            'progress_percentage': 30,
            'current_category': 'Visa Application',
            'next_tasks': ['Schedule interview', 'Prepare documents']
        }
        
        # Get recommendations from OpenAI service
        result = await openai_service.get_personalized_recommendations(
            user=mock_user,
            current_checklist_progress=current_progress
        )
        
        if result['success']:
            return {
                "message": "Test recommendations generated successfully",
                "recommendations": result['recommendations'],
                "generated_at": result['generated_at'],
                "fallback_used": result.get('fallback_used', False)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate test recommendations: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(f"Error in test recommendations generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.post("/test-tips", response_model=Dict[str, Any])
async def test_get_tips():
    """
    Test endpoint to get smart tips without authentication.
    This is for testing purposes only.
    """
    logger.info("Testing AI tips generation")
    
    try:
        # Create a mock user for testing
        from app.models.user import User
        
        # Mock user data
        mock_user = User(
            id="test-user-123",
            cognito_sub="test-cognito-sub",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            birthdate="1994-01-01",
            onboarding_complete=True,
            is_active=True,
            is_verified=True
        )
        
        # Mock task and context
        current_task = "Preparing for visa interview"
        context = {
            "visa_type": "Work Visa",
            "destination_country": "Canada",
            "interview_date": "2024-02-15"
        }
        
        # Get tips from OpenAI service
        result = await openai_service.get_smart_tips(
            user=mock_user,
            current_task=current_task,
            context=context
        )
        
        if result['success']:
            return {
                "message": "Test tips generated successfully",
                "tips": result['tips'],
                "generated_at": result['generated_at'],
                "fallback_used": result.get('fallback_used', False)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate test tips: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(f"Error in test tips generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        ) 