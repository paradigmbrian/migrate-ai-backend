"""
Main FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import init_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("Starting MigrateAI Backend...")
    
    # Initialize database connection
    await init_db()
    print("Database initialized successfully")
    
    yield
    
    print("Shutting down MigrateAI Backend...")


# Create FastAPI app
app = FastAPI(
    title="MigrateAI Backend",
    description="Backend API for MigrateAI - Immigration checklist and guidance platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MigrateAI Backend API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    # Load local environment if available
    if os.path.exists(".env.local"):
        from dotenv import load_dotenv
        load_dotenv(".env.local")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 