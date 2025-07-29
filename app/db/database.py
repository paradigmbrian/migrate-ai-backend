"""
Database configuration and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection and verify tables exist.
    Note: Tables are now managed by Alembic migrations.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models import user, checklist, country, policy  # noqa
        
        # Verify database connection
        await conn.execute(text("SELECT 1"))
        print("Database initialized successfully") 