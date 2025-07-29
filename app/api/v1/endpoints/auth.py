"""
Authentication endpoints for user login and registration.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin
from app.schemas.user import UserResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if user already exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        age=user_data.age,
        marital_status=user_data.marital_status,
        profession=user_data.profession,
        dependents=user_data.dependents,
        origin_country_code=user_data.origin_country_code,
        destination_country_code=user_data.destination_country_code,
        reason_for_moving=user_data.reason_for_moving,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return access token.
    """
    # Find user by email
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.post("/demo-login", response_model=Token)
async def demo_login(
    db: AsyncSession = Depends(get_db)
):
    """
    Demo login for development/testing purposes.
    """
    # Find or create demo user
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == "demo@example.com"))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create demo user
        hashed_password = get_password_hash("demo123")
        user = User(
            email="demo@example.com",
            hashed_password=hashed_password,
            first_name="Demo",
            last_name="User",
            age=30,
            marital_status="single",
            profession="Software Engineer",
            dependents=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    } 