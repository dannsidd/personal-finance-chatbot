from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "Personal Finance Chatbot"
    version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Database - SQLite only
    database_url: str = "sqlite:///./finance_chatbot.db"
    secret_key: str = "your-super-secret-key-change-in-production"
    
    # HuggingFace (Optional - for enhanced models)
    huggingface_api_key: Optional[str] = None
    
    # CORS
    cors_origins: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    # Email (for notifications)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # JWT
    jwt_secret: str = "jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File uploads
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Granite Model Settings - UPDATED FOR 2B BASE
    granite_model_name: str = "ibm-granite/granite-3.3-2b-base"
    granite_device: str = "auto"
    granite_max_tokens: int = 512  # Conservative for 2B model
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
