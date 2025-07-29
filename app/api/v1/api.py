"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, checklists, countries, policies

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(checklists.router, prefix="/checklists", tags=["checklists"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"]) 