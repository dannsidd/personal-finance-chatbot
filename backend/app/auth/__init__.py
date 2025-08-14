"""
Authentication module for Personal Finance Chatbot
Handles user registration, login, JWT tokens, and user management
"""

from app.auth.routes import router as auth_router
from app.auth.models import UserCreate, UserResponse, UserLogin, Token, UserUpdate

__all__ = [
    "auth_router",
    "UserCreate",
    "UserResponse", 
    "UserLogin",
    "Token",
    "UserUpdate"
]
