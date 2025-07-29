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
    secret_key: str = Field(..., alias="SECRET_KEY", description="Secret key for JWT tokens")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
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
    
    # MCP Server
    mcp_server_url: str = Field(
        default="http://localhost:8001", 
        alias="MCP_SERVER_URL",
        description="MCP server URL for data collection"
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