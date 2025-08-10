"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import cognito_auth, users, checklists, countries, policies, data_collection, profile, ai_checklists, policy_monitoring, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(cognito_auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profile.router, prefix="/users", tags=["profile"])
api_router.include_router(checklists.router, prefix="/checklists", tags=["checklists"])
api_router.include_router(ai_checklists.router, prefix="/ai-checklists", tags=["ai-checklists"])
api_router.include_router(policy_monitoring.router, prefix="/policy-monitoring", tags=["policy-monitoring"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(data_collection.router, prefix="/data-collection", tags=["data-collection"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 