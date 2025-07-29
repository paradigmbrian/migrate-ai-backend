"""
User model for authentication and user management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    marital_status = Column(String(50), nullable=True)
    profession = Column(String(200), nullable=True)
    dependents = Column(Integer, default=0)
    
    # Migration details
    origin_country_code = Column(String(3), nullable=True)
    destination_country_code = Column(String(3), nullable=True)
    reason_for_moving = Column(Text, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    checklists = relationship("Checklist", back_populates="user", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>" 