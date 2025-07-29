"""
User management endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current user profile."""
    return {"message": "Get current user - TODO"}


@router.put("/me")
async def update_current_user():
    """Update current user profile."""
    return {"message": "Update current user - TODO"} 