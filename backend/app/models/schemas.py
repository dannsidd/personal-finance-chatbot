from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# Enums
class PersonaType(str, Enum):
    STUDENT = "student"
    PROFESSIONAL = "professional"
    FAMILY = "family"

class DebtStrategy(str, Enum):
    AVALANCHE = "avalanche"
    SNOWBALL = "snowball"
    HYBRID = "hybrid"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

# Base Models
class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# Authentication Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    persona_preference: PersonaType = PersonaType.STUDENT
    language_preference: str = "en"

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    persona_preference: Optional[PersonaType] = None
    language_preference: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# NLU Models
class NLURequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = "en"

class NLUResponse(BaseModel):
    intent: Optional[str] = None
    entities: List[Dict[str, Any]] = []
    sentiment: Dict[str, Union[float, str]] = {}
    emotion: Dict[str, float] = {}
    keywords: List[Dict[str, Any]] = []
    confidence: float = 0.0

# LLM Models
class ChatMessage(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_items=1)
    persona: PersonaType = PersonaType.STUDENT
    language: str = "en"
    reasoning: bool = False
    max_tokens: int = Field(default=1024, ge=100, le=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    context: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    text: str
    model_used: str
    persona: PersonaType
    language: str
    reasoning_used: bool
    token_count: Optional[int] = None
    finish_reason: Optional[str] = None

# Chat History Models
class ChatSessionCreate(BaseModel):
    session_name: str = Field(..., min_length=1, max_length=200)
    persona: PersonaType = PersonaType.STUDENT
    language: str = "en"

class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    session_name: str
    persona_used: str
    language_used: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    message_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Budget Models
class Transaction(BaseModel):
    date: datetime
    description: str = Field(..., min_length=1, max_length=500)
    amount: float
    category: Optional[str] = None
    
    @validator('amount')
    def amount_not_zero(cls, v):
        if v == 0:
            raise ValueError('Amount cannot be zero')
        return v

class BudgetAnalysisRequest(BaseModel):
    transactions: List[Transaction] = Field(..., min_items=1)
    analysis_name: Optional[str] = "Budget Analysis"
    include_insights: bool = True
    include_recommendations: bool = True

class BudgetInsight(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    amount: Optional[float] = None
    percentage: Optional[float] = None
    evidence: Dict[str, Any] = {}
    type: str = "general"

class BudgetRecommendation(BaseModel):
    title: str
    description: str
    action: str
    category: Optional[str] = None
    potential_savings: Optional[float] = None
    priority: str = "medium"
    type: str = "general"

class BudgetAnalysisResponse(BaseModel):
    summary: Dict[str, Any]
    categories: Dict[str, float]
    anomalies: List[Dict[str, Any]] = []
    insights: List[BudgetInsight] = []
    recommendations: List[BudgetRecommendation] = []
    trends: Dict[str, Any] = {}
    analysis_id: Optional[uuid.UUID] = None

# Debt Models
class DebtAccount(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    balance: float = Field(..., gt=0)
    apr: float = Field(..., ge=0, le=50)
    minimum_payment: float = Field(..., gt=0)
    
    @validator('minimum_payment')
    def validate_minimum_payment(cls, v, values):
        if 'balance' in values and v > values['balance']:
            raise ValueError('Minimum payment cannot exceed balance')
        return v

class DebtPlanRequest(BaseModel):
    debts: List[DebtAccount] = Field(..., min_items=1)
    extra_payment: float = Field(default=0.0, ge=0)
    strategy: DebtStrategy = DebtStrategy.AVALANCHE

class DebtPlanResponse(BaseModel):
    summary: Dict[str, Any]
    savings: Dict[str, Any]
    payoff_plan: List[Dict[str, Any]]
    baseline_plan: List[Dict[str, Any]]
    insights: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    next_action: str
    milestones: List[Dict[str, Any]] = []

# Goal Models
class FinancialGoal(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_amount: float = Field(..., gt=0)
    timeline_months: int = Field(..., ge=1, le=600)  # Max 50 years
    priority: int = Field(default=3, ge=1, le=10)
    category: Optional[str] = None

class GoalPlanRequest(BaseModel):
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    goals: List[FinancialGoal] = Field(..., min_items=1)
    
    @validator('monthly_expenses')
    def validate_expenses(cls, v, values):
        if 'monthly_income' in values and v > values['monthly_income'] * 2:
            raise ValueError('Monthly expenses seem unreasonably high')
        return v

class GoalPlanResponse(BaseModel):
    financial_overview: Dict[str, Any]
    goal_analysis: Dict[str, Any]
    individual_goals: Dict[str, Any]
    optimized_plan: Dict[str, Any]
    insights: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    milestones: List[Dict[str, Any]] = []
    action_plan: Dict[str, Any]

# Multilingual Models
class LanguageDetectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class LanguageDetectionResponse(BaseModel):
    language: str
    confidence: float
    supported: bool = True

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    source_language: str = "auto"
    target_language: str = "en"

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 1.0

# File Upload Models
class FileUploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str
    upload_id: uuid.UUID
    status: str = "uploaded"

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Health Check
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = {}

