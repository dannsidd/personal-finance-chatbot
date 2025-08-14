"""
Services module for Personal Finance Chatbot
Contains all AI and financial analysis services
"""
from app.services.multilingual import multilingual_service
from app.services.budget_analyzer import budget_analyzer
from app.services.debt_planner import debt_planner
from app.services.goal_planner import goal_planner
from app.services.chat_history import chat_history_service

# Service registry for easy access
SERVICES = {
    "multilingual": multilingual_service,
    "budget_analyzer": budget_analyzer,
    "debt_planner": debt_planner,
    "goal_planner": goal_planner,
    "chat_history": chat_history_service
}

def get_service(service_name: str):
    """Get a service by name"""
    return SERVICES.get(service_name)

def get_all_services():
    """Get all available services"""
    return SERVICES

__all__ = [ 
    "multilingual_service",
    "budget_analyzer",
    "debt_planner",
    "goal_planner",
    "chat_history_service",
    "SERVICES",
    "get_service",
    "get_all_services"
]
