"""
Models module for Personal Finance Chatbot
Contains Pydantic schemas and SQLAlchemy database models
"""

# Import database models
from app.models.database_models import (
    User,
    ChatSession,
    ChatMessage,
    UserFinancialProfile,
    BudgetAnalysis,
    UserScenarioData,
    Base
)

# Import Pydantic schemas
from app.models.schemas import (
    # Auth models
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
    # Chat models
    ChatMessage as ChatMessageSchema,
    LLMRequest,
    LLMResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    # Budget models
    Transaction,
    BudgetAnalysisRequest,
    BudgetAnalysisResponse,
    BudgetInsight,
    BudgetRecommendation,
    # Debt models
    DebtAccount,
    DebtPlanRequest,
    DebtPlanResponse,
    # Goal models
    FinancialGoal,
    GoalPlanRequest,
    GoalPlanResponse,
    # NLU models
    NLURequest,
    NLUResponse,
    # Utility models
    ErrorResponse,
    HealthResponse
)

# Database models
DATABASE_MODELS = [
    User,
    ChatSession,
    ChatMessage,
    UserFinancialProfile,
    BudgetAnalysis,
    UserScenarioData
]

# Pydantic schemas organized by category
AUTH_SCHEMAS = [UserCreate, UserResponse, UserUpdate, Token]
CHAT_SCHEMAS = [ChatMessageSchema, LLMRequest, LLMResponse, ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse]
BUDGET_SCHEMAS = [Transaction, BudgetAnalysisRequest, BudgetAnalysisResponse, BudgetInsight, BudgetRecommendation]
DEBT_SCHEMAS = [DebtAccount, DebtPlanRequest, DebtPlanResponse]
GOAL_SCHEMAS = [FinancialGoal, GoalPlanRequest, GoalPlanResponse]
NLU_SCHEMAS = [NLURequest, NLUResponse]
UTILITY_SCHEMAS = [ErrorResponse, HealthResponse]

__all__ = [
    # Database models
    "User",
    "ChatSession", 
    "ChatMessage",
    "UserFinancialProfile",
    "BudgetAnalysis",
    "UserScenarioData",
    "Base",
    "DATABASE_MODELS",
    
    # Pydantic schemas
    "UserCreate",
    "UserResponse",
    "UserUpdate", 
    "Token",
    "ChatMessageSchema",
    "LLMRequest",
    "LLMResponse",
    "ChatSessionCreate",
    "ChatSessionResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "Transaction",
    "BudgetAnalysisRequest",
    "BudgetAnalysisResponse",
    "BudgetInsight",
    "BudgetRecommendation",
    "DebtAccount",
    "DebtPlanRequest",
    "DebtPlanResponse",
    "FinancialGoal",
    "GoalPlanRequest",
    "GoalPlanResponse",
    "NLURequest",
    "NLUResponse",
    "ErrorResponse",
    "HealthResponse",
    
    # Schema collections
    "AUTH_SCHEMAS",
    "CHAT_SCHEMAS",
    "BUDGET_SCHEMAS", 
    "DEBT_SCHEMAS",
    "GOAL_SCHEMAS",
    "NLU_SCHEMAS",
    "UTILITY_SCHEMAS"
]
