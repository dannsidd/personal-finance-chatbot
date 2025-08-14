"""
Utilities module for Personal Finance Chatbot Frontend
Helper functions and utilities for the Streamlit application
"""

from utils.api_client import APIClient, APIError
from utils.theme import apply_custom_theme, get_theme_colors
from utils.helpers import (
    format_currency,
    format_date,
    format_percentage,
    get_user_avatar,
    validate_email,
    sanitize_input,
    generate_colors,
    create_download_link,
    show_loading_spinner,
    display_error_message,
    display_success_message
)

# Configuration
DEFAULT_API_BASE_URL = "http://localhost:8000"
DEFAULT_THEME = "modern"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "ta": "தமிழ்", 
    "te": "తెలుగు",
    "bn": "বাংলা",
    "gu": "ગુજરાતી",
    "mr": "मराठी",
    "es": "Español",
    "fr": "Français"
}

SUPPORTED_PERSONAS = {
    "student": {
        "emoji": "🎓",
        "display": "Student",
        "description": "Student or early career professional"
    },
    "professional": {
        "emoji": "💼", 
        "display": "Professional",
        "description": "Working professional"
    },
    "family": {
        "emoji": "👨‍👩‍👧‍👦",
        "display": "Family",
        "description": "Family financial manager"
    }
}

# Utility functions
def get_api_client(base_url: str = None) -> APIClient:
    """Get configured API client"""
    return APIClient(base_url or DEFAULT_API_BASE_URL)

def get_supported_languages():
    """Get list of supported languages"""
    return SUPPORTED_LANGUAGES

def get_supported_personas():
    """Get list of supported personas"""
    return SUPPORTED_PERSONAS

def format_persona_display(persona: str) -> str:
    """Format persona for display"""
    persona_info = SUPPORTED_PERSONAS.get(persona, {})
    emoji = persona_info.get("emoji", "👤")
    display = persona_info.get("display", persona.title())
    return f"{emoji} {display}"

def format_language_display(language: str) -> str:
    """Format language for display"""
    return SUPPORTED_LANGUAGES.get(language, language.upper())

__all__ = [
    # API client
    "APIClient",
    "APIError",
    "get_api_client",
    
    # Theme
    "apply_custom_theme",
    "get_theme_colors",
    
    # Helpers
    "format_currency",
    "format_date",
    "format_percentage",
    "get_user_avatar",
    "validate_email", 
    "sanitize_input",
    "generate_colors",
    "create_download_link",
    "show_loading_spinner",
    "display_error_message",
    "display_success_message",
    
    # Configuration
    "DEFAULT_API_BASE_URL",
    "DEFAULT_THEME",
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_PERSONAS",
    
    # Utility functions
    "get_supported_languages",
    "get_supported_personas", 
    "format_persona_display",
    "format_language_display"
]
