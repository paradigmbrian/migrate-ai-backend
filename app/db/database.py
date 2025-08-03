"""
Database configuration and session management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize database connection.
    Tables are created via Alembic migrations.
    """
    try:
        # Verify database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise 