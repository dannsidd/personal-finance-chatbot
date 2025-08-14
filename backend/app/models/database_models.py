from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    persona_preference = Column(String, default="student")
    language_preference = Column(String, default="en")
    storage_preference = Column(String, default="cloud")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    financial_profile = relationship("UserFinancialProfile", back_populates="user", uselist=False)
    budget_analyses = relationship("BudgetAnalysis", back_populates="user")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    session_name = Column(String, nullable=False)
    persona_used = Column(String, nullable=False)
    language_used = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")
    extra_metadata = Column('metadata', JSON, nullable=True)  # ✅ This should be fixed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")



class UserFinancialProfile(Base):
    __tablename__ = "user_financial_profiles"
    
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    monthly_income = Column(Float)
    monthly_expenses = Column(Float)
    financial_goals = Column(JSON)
    debt_accounts = Column(JSON)
    budget_categories = Column(JSON)
    investment_preferences = Column(JSON)
    risk_tolerance = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="financial_profile")

class BudgetAnalysis(Base):
    __tablename__ = "budget_analyses"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    analysis_name = Column(String)
    transactions_count = Column(Float)
    total_spending = Column(Float)
    categories = Column(JSON)
    insights = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="budget_analyses")

class UserScenarioData(Base):
    __tablename__ = "user_scenario_data"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    scenario_name = Column(String, nullable=False)
    scenario_data = Column(JSON)
    analysis_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

