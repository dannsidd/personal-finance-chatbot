from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import logging
from uuid import uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd
import io

# Internal imports
from app.config import settings
from app.database import get_db, create_tables
from app.models.schemas import *
from app.auth.routes import router as auth_router, get_current_user
from app.models.database_models import User as UserModel

# Services
from app.services.granite_huggingface_service import granite_huggingface_service
from app.services.multilingual import multilingual_service
from app.services.budget_analyzer import budget_analyzer
from app.services.debt_planner import debt_planner
from app.services.goal_planner import goal_planner
from app.services.chat_history import chat_history_service

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered personal finance guidance with multilingual support",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Security
security = HTTPBearer()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.streamlit.app", "*.ibm.com"]
)

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["authentication"]
)

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Application health check"""
    services_status = {
        "database": "connected",
        "granite_huggingface": "available",
        "multilingual": "available"
    }
    
    # Check if Granite models are loaded
    try:
        if hasattr(granite_huggingface_service, 'model') and granite_huggingface_service.model:
            services_status["granite_model"] = "loaded"
        else:
            services_status["granite_model"] = "not_loaded"
    except:
        services_status["granite_model"] = "error"
    
    return HealthResponse(
        status="healthy",
        version=settings.version,
        services=services_status
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs" if settings.debug else "Not available in production"
    }

# NLU Endpoints
@app.post(f"{settings.api_prefix}/nlu/analyze", response_model=NLUResponse)
async def analyze_text(
    request: NLURequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Analyze text using Granite NLU"""
    try:
        result = await granite_huggingface_service.analyze_text(request.text, request.language)
        return NLUResponse(**result)
    except Exception as e:
        logger.error(f"NLU analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Text analysis failed")

# Language Detection
@app.post(f"{settings.api_prefix}/language/detect", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """Detect language of input text"""
    try:
        result = await multilingual_service.detect_language(request.text)
        return LanguageDetectionResponse(
            language=result["language"],
            confidence=result["confidence"],
            supported=result["language"] in ["en", "hi", "ta", "te", "bn", "gu", "mr", "es", "fr"]
        )
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail="Language detection failed")

# LLM Chat Endpoints
# In your chat endpoint, add timeout handling
# LLM Chat Endpoints
@app.post(f"{settings.api_prefix}/chat/generate", response_model=LLMResponse)
async def generate_chat_response(
    request: LLMRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Generate AI chat response using Granite from HuggingFace"""
    try:
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Convert messages to dict format
        messages = [msg.dict() for msg in request.messages]
        
        context = request.context or {}
        context.update({
            "user_persona": current_user.persona_preference,
            "user_language": current_user.language_preference
        })
        
        # Test if Granite service is available
        if not hasattr(granite_huggingface_service, 'model') or granite_huggingface_service.model is None:
            raise HTTPException(status_code=503, detail="AI model not available")
        
        # Set a reasonable timeout for CPU inference
        import asyncio
        result = await asyncio.wait_for(
            granite_huggingface_service.generate_response(
                messages=messages,
                persona=request.persona,
                language=request.language,
                reasoning=request.reasoning,
                context=context
            ),
            timeout=120.0  # 2 minutes for CPU inference
        )
        
        # Validate response format
        if not isinstance(result, dict):
            result = {"text": str(result), "model_used": "granite-3.3-2b-base"}
        
        if "text" not in result:
            result["text"] = "I received your message but had trouble generating a response."
        
        return LLMResponse(**result)
        
    except asyncio.TimeoutError:
        # Return fallback response instead of complete failure
        logger.warning("Chat generation timed out, returning fallback response")
        return LLMResponse(
            text="I'm taking longer than usual to process your request. This is normal for CPU inference. Let me give you a quick response: I'm your AI finance assistant and I'm here to help with budgeting, debt management, investments, and financial planning. What specific financial question can I help you with?",
            model_used="granite-3.3-2b-base-timeout-fallback",
            persona=request.persona,
            language=request.language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat generation failed: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Chat response generation failed: {str(e)}")



# Chat History Endpoints
@app.post(f"{settings.api_prefix}/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new chat session"""
    try:
        session = await chat_history_service.create_chat_session(
            db=db,
            user_id=current_user.id,
            session_name=request.session_name,
            persona=request.persona,
            language=request.language
        )
        
        return ChatSessionResponse(
            id=session.id,
            session_name=session.session_name,
            persona_used=session.persona_used,
            language_used=session.language_used,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")

@app.get(f"{settings.api_prefix}/chat/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    limit: int = 20,
    include_archived: bool = False,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    try:
        sessions = await chat_history_service.get_user_sessions(
            db=db,
            user_id=current_user.id,
            limit=limit,
            include_archived=include_archived
        )
        
        return [
            ChatSessionResponse(
                id=session.id,
                session_name=session.session_name,
                persona_used=session.persona_used,
                language_used=session.language_used,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=len(session.messages) if hasattr(session, 'messages') else 0
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Getting sessions failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat sessions")

@app.post(f"{settings.api_prefix}/chat/sessions/{{session_id}}/messages", response_model=ChatMessageResponse)
async def add_message_to_session(
    session_id: str,  # Changed from uuid.UUID to str for compatibility
    request: ChatMessageCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add message to chat session"""
    try:
        message = await chat_history_service.add_message_to_session(
            db=db,
            session_id=session_id,
            role=request.role,
            content=request.content,
            message_type=request.message_type,
            metadata=request.metadata
        )
        
        return ChatMessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at,
            extra_metadata=message.extra_metadata  # Updated field name
        )
        
    except Exception as e:
        logger.error(f"Adding message failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")

@app.get(f"{settings.api_prefix}/chat/sessions/{{session_id}}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,  # Changed from uuid.UUID to str for compatibility
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from chat session"""
    try:
        messages = await chat_history_service.get_session_messages(
            db=db,
            session_id=session_id,
            limit=limit
        )
        
        return [
            ChatMessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                message_type=message.message_type,
                created_at=message.created_at,
                extra_metadata=message.extra_metadata  # Updated field name
            )
            for message in messages
        ]
        
    except Exception as e:
        logger.error(f"Getting messages failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

# Budget Analysis Endpoints
@app.post(f"{settings.api_prefix}/budget/analyze", response_model=BudgetAnalysisResponse)
async def analyze_budget(
    request: BudgetAnalysisRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze budget from transactions"""
    try:
        # Convert transactions to dict format
        transactions = [txn.dict() for txn in request.transactions]
        
        # Add user context
        user_context = {
            "persona": current_user.persona_preference,
            "language": current_user.language_preference
        }
        
        result = await budget_analyzer.analyze_budget(transactions, user_context)
        
        # Store analysis in database
        analysis_id = str(uuid.uuid4())  # Convert to string
        # TODO: Store in database
        
        return BudgetAnalysisResponse(
            analysis_id=analysis_id,
            **result
        )
        
    except Exception as e:
        logger.error(f"Budget analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Budget analysis failed")

# Debt Planning Endpoints
@app.post(f"{settings.api_prefix}/debt/plan", response_model=DebtPlanResponse)
async def create_debt_plan(
    request: DebtPlanRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Create debt payoff plan"""
    try:
        # Convert debts to dict format
        debts = [debt.dict() for debt in request.debts]
        
        user_context = {
            "persona": current_user.persona_preference,
            "language": current_user.language_preference
        }
        
        result = await debt_planner.create_debt_plan(
            debts=debts,
            extra_payment=request.extra_payment,
            strategy=request.strategy,
            user_context=user_context
        )
        
        return DebtPlanResponse(**result)
        
    except Exception as e:
        logger.error(f"Debt planning failed: {e}")
        raise HTTPException(status_code=500, detail="Debt planning failed")

# Goal Planning Endpoints
@app.post(f"{settings.api_prefix}/goals/plan", response_model=GoalPlanResponse)
async def create_goal_plan(
    request: GoalPlanRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """Create financial goal plan"""
    try:
        # Convert goals to dict format
        goals = [goal.dict() for goal in request.goals]
        
        user_context = {
            "persona": current_user.persona_preference,
            "language": current_user.language_preference
        }
        
        result = await goal_planner.create_goal_plan(
            income=request.monthly_income,
            expenses=request.monthly_expenses,
            goals=goals,
            user_context=user_context
        )
        
        return GoalPlanResponse(**result)
        
    except Exception as e:
        logger.error(f"Goal planning failed: {e}")
        raise HTTPException(status_code=500, detail="Goal planning failed")

# File Upload Endpoints
@app.post(f"{settings.api_prefix}/upload/transactions", response_model=BudgetAnalysisResponse)
async def upload_transactions_csv(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    """Upload and analyze transactions from CSV file"""
    try:
        # Validate file
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file size
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Parse CSV
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['date', 'description', 'amount']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {', '.join(required_columns)}"
            )
        
        # Convert to transactions
        transactions = []
        for _, row in df.iterrows():
            try:
                transactions.append({
                    'date': pd.to_datetime(row['date']).isoformat(),
                    'description': str(row['description']),
                    'amount': float(row['amount'])
                })
            except Exception as e:
                logger.warning(f"Skipping invalid transaction row: {e}")
                continue
        
        if not transactions:
            raise HTTPException(status_code=400, detail="No valid transactions found in file")
        
        # Analyze budget
        user_context = {
            "persona": current_user.persona_preference,
            "language": current_user.language_preference
        }
        
        result = await budget_analyzer.analyze_budget(transactions, user_context)
        
        return BudgetAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File processing failed")

# Error handlers - FIXED JSON serialization issues
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper JSON serialization"""
    try:
        # Use jsonable_encoder to handle datetime objects
        content = jsonable_encoder({
            "error": exc.__class__.__name__,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    except Exception as e:
        logger.error(f"Error in HTTP exception handler: {e}")
        # Fallback response without datetime
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": str(exc.detail),
                "status_code": exc.status_code
            }
        )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper JSON serialization"""
    try:
        logger.error(f"Unhandled exception: {exc}")
        
        # Use jsonable_encoder for proper serialization
        content = jsonable_encoder({
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return JSONResponse(
            status_code=500,
            content=content
        )
    except Exception as e:
        logger.error(f"Error in general exception handler: {e}")
        # Minimal fallback response
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
