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
from pathlib import Path
import json


async def seed_countries(session: AsyncSession) -> None:
    """Seed countries data."""
    
    # Check if countries already exist
    existing_countries = await session.execute(text("SELECT COUNT(*) FROM countries"))
    if existing_countries.scalar() > 0:
        print("Countries already seeded, skipping...")
        return
    
    # Read countries from JSON file
    countries_file = Path(__file__).parent / "data" / "countries.json"
    if not countries_file.exists():
        print("Countries data file not found, skipping...")
        return
    
    with open(countries_file, 'r') as f:
        countries_data = json.load(f)
    
    for country_data in countries_data:
        country = Country(**country_data)
        session.add(country)
    
    await session.commit()
    print(f"Seeded {len(countries_data)} countries")


async def seed_policies(session: AsyncSession) -> None:
    """Seed immigration policies data."""
    
    # Check if policies already exist
    existing_policies = await session.execute(text("SELECT COUNT(*) FROM policies"))
    if existing_policies.scalar() > 0:
        print("Policies already seeded, skipping...")
        return
    
    # Read policies from JSON file
    policies_file = Path(__file__).parent / "data" / "policies.json"
    if not policies_file.exists():
        print("Policies data file not found, skipping...")
        return
    
    with open(policies_file, 'r') as f:
        policies_data = json.load(f)
    
    for policy_data in policies_data:
        policy = Policy(**policy_data)
        session.add(policy)
    
    await session.commit()
    print(f"Seeded {len(policies_data)} policies")


async def seed_database():
    """Seed the database with initial data."""
    async with AsyncSessionLocal() as session:
        try:
            print("Starting database seeding...")
            
            await seed_countries(session)
            await seed_policies(session)
            
            print("Database seeding completed!")
            
        except Exception as e:
            print(f"Error seeding database: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_database()) 