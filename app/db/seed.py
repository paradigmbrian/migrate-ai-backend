"""
Database seeding script for initial data.
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import AsyncSessionLocal
from app.models.country import Country
from app.models.user import User
from app.models.checklist import Checklist, ChecklistItem
from app.models.policy import Policy
from app.core.security import get_password_hash


async def seed_countries(session: AsyncSession) -> None:
    """Seed countries table with initial data."""
    
    countries_data = [
        {
            "code": "USA",
            "name": "United States",
            "flag_emoji": "🇺🇸",
            "region": "North America",
            "latitude": 37.0902,
            "longitude": -95.7129,
            "timezone": "UTC-5",
            "currency_code": "USD",
            "currency_name": "US Dollar",
            "gdp_per_capita": 69287.5,
            "visa_required": True,
            "visa_types": "Tourist, Business, Student, Work, Family",
            "processing_time_days": 30,
            "application_fee_usd": 160,
            "is_active": True,
        },
        {
            "code": "CAN",
            "name": "Canada",
            "flag_emoji": "🇨🇦",
            "region": "North America",
            "latitude": 56.1304,
            "longitude": -106.3468,
            "timezone": "UTC-6",
            "currency_code": "CAD",
            "currency_name": "Canadian Dollar",
            "gdp_per_capita": 51988.0,
            "visa_required": True,
            "visa_types": "Tourist, Business, Student, Work, Express Entry",
            "processing_time_days": 45,
            "application_fee_usd": 100,
            "is_active": True,
        },
        {
            "code": "GBR",
            "name": "United Kingdom",
            "flag_emoji": "🇬🇧",
            "region": "Europe",
            "latitude": 55.3781,
            "longitude": -3.4360,
            "timezone": "UTC+0",
            "currency_code": "GBP",
            "currency_name": "British Pound",
            "gdp_per_capita": 46510.0,
            "visa_required": True,
            "visa_types": "Tourist, Business, Student, Work, Family",
            "processing_time_days": 60,
            "application_fee_usd": 120,
            "is_active": True,
        },
        {
            "code": "AUS",
            "name": "Australia",
            "flag_emoji": "🇦🇺",
            "region": "Oceania",
            "latitude": -25.2744,
            "longitude": 133.7751,
            "timezone": "UTC+10",
            "currency_code": "AUD",
            "currency_name": "Australian Dollar",
            "gdp_per_capita": 60443.0,
            "visa_required": True,
            "visa_types": "Tourist, Business, Student, Work, Skilled Migration",
            "processing_time_days": 90,
            "application_fee_usd": 140,
            "is_active": True,
        },
        {
            "code": "DEU",
            "name": "Germany",
            "flag_emoji": "🇩🇪",
            "region": "Europe",
            "latitude": 51.1657,
            "longitude": 10.4515,
            "timezone": "UTC+1",
            "currency_code": "EUR",
            "currency_name": "Euro",
            "gdp_per_capita": 51200.0,
            "visa_required": True,
            "visa_types": "Tourist, Business, Student, Work, Blue Card",
            "processing_time_days": 45,
            "application_fee_usd": 80,
            "is_active": True,
        },
    ]
    
    for country_data in countries_data:
        # Check if country already exists by code
        existing = await session.execute(
            text("SELECT id FROM countries WHERE code = :code"),
            {"code": country_data["code"]}
        )
        if not existing.scalar():
            country = Country(**country_data)
            session.add(country)
    
    await session.commit()
    print(f"Seeded {len(countries_data)} countries")


async def seed_demo_users(session: AsyncSession) -> None:
    """Seed demo users for testing."""
    
    demo_users = [
        {
            "email": "demo@migrate.ai",
            "hashed_password": get_password_hash("demo123"),
            "first_name": "Demo",
            "last_name": "User",
            "age": 30,
            "marital_status": "Single",
            "profession": "Software Engineer",
            "dependents": 0,
            "origin_country_code": "USA",
            "destination_country_code": "CAN",
            "reason_for_moving": "Career opportunity",
            "is_active": True,
            "is_verified": True,
        },
        {
            "email": "test@migrate.ai",
            "hashed_password": get_password_hash("test123"),
            "first_name": "Test",
            "last_name": "User",
            "age": 28,
            "marital_status": "Married",
            "profession": "Data Scientist",
            "dependents": 1,
            "origin_country_code": "GBR",
            "destination_country_code": "AUS",
            "reason_for_moving": "Better quality of life",
            "is_active": True,
            "is_verified": True,
        },
    ]
    
    for user_data in demo_users:
        # Check if user already exists
        existing = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data["email"]}
        )
        if not existing.scalar():
            user = User(**user_data)
            session.add(user)
    
    await session.commit()
    print(f"Seeded {len(demo_users)} demo users")


async def seed_database() -> None:
    """Main seeding function."""
    async with AsyncSessionLocal() as session:
        print("Starting database seeding...")
        
        await seed_countries(session)
        await seed_demo_users(session)
        
        print("Database seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_database()) 