"""
Country data endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_countries():
    """Get all countries."""
    return {"message": "Get countries - TODO"}


@router.get("/{country_code}")
async def get_country(country_code: str):
    """Get specific country."""
    return {"message": f"Get country {country_code} - TODO"}


@router.get("/{country_code}/policies")
async def get_country_policies(country_code: str):
    """Get policies for specific country."""
    return {"message": f"Get policies for {country_code} - TODO"} 