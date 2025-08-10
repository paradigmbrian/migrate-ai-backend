"""
Country model for storing country information and data.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from app.db.database import Base


class Country(Base):
    """Country model for storing country information."""
    
    __tablename__ = "countries"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(3), unique=True, index=True, nullable=False)  # ISO 3166-1 alpha-3
    name = Column(String(100), nullable=False)
    flag_emoji = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True)
    
    # Geographic information
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Economic information
    currency_code = Column(String(3), nullable=True)
    currency_name = Column(String(50), nullable=True)
    gdp_per_capita = Column(Float, nullable=True)
    
    # Immigration information
    visa_required = Column(Boolean, nullable=True)
    visa_types = Column(Text, nullable=True)  # JSON string of available visa types
    processing_time_days = Column(Integer, nullable=True)
    application_fee_usd = Column(Float, nullable=True)
    
    # Data freshness
    policies_last_updated = Column(DateTime, nullable=True)
    data_source = Column(String(200), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    immigration_requirements = relationship("ImmigrationRequirements", back_populates="country")
    country_data = relationship("CountryData", back_populates="country")
    
    def __repr__(self) -> str:
        return f"<Country(code='{self.code}', name='{self.name}')>" 