"""
Configuration settings for the MigrateAI backend.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "MigrateAI Backend"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, alias="DEBUG", description="Enable debug mode")
    
    # API
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(..., alias="SECRET_KEY", description="Secret key for application")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL", description="Backend URL for OAuth callbacks")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL", description="PostgreSQL database URL")
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL", description="Redis URL")
    
    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8081"],
        alias="ALLOWED_ORIGINS",
        description="Allowed CORS origins"
    )
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY", description="OpenAI API key")
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID", description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY", description="AWS secret access key")
    
    # AWS Cognito Configuration
    cognito_user_pool_id: Optional[str] = Field(default=None, alias="COGNITO_USER_POOL_ID", description="Cognito User Pool ID")
    cognito_client_id: Optional[str] = Field(default=None, alias="COGNITO_CLIENT_ID", description="Cognito App Client ID")
    cognito_client_secret: Optional[str] = Field(default=None, alias="COGNITO_CLIENT_SECRET", description="Cognito App Client Secret")
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID", description="Google OAuth Client ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET", description="Google OAuth Client Secret")
    
    # Data Collection
    data_collection_timeout: int = Field(
        default=30,
        alias="DATA_COLLECTION_TIMEOUT",
        description="Timeout for data collection requests in seconds"
    )
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Global settings instance
settings = Settings() 