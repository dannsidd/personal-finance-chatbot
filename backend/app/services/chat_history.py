from sqlalchemy.orm import Session
from app.models.database_models import ChatSession, ChatMessage, User
from typing import List, Optional, Dict
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class ChatHistoryService:
    def __init__(self):
        pass
    
    async def create_chat_session(
        self, 
        db: Session, 
        user_id: uuid.UUID, 
        session_name: str,
        persona: str = "student",
        language: str = "en"
    ) -> ChatSession:
        """Create a new chat session"""
        try:
            session = ChatSession(
                user_id=user_id,
                session_name=session_name,
                persona_used=persona,
                language_used=language
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            logger.info(f"Created chat session {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            db.rollback()
            raise
    
    async def add_message_to_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """Add a message to existing chat session"""
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata=metadata or {}
            )
            
            db.add(message)
            
            # Update session timestamp
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(message)
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message to session: {e}")
            db.rollback()
            raise
    
    async def get_user_sessions(
        self,
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
        include_archived: bool = False
    ) -> List[ChatSession]:
        """Get user's chat sessions"""
        try:
            query = db.query(ChatSession).filter(ChatSession.user_id == user_id)
            
            if not include_archived:
                query = query.filter(ChatSession.is_archived == False)
            
            sessions = query.order_by(ChatSession.updated_at.desc()).limit(limit).all()
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    async def get_session_messages(
        self,
        db: Session,
        session_id: uuid.UUID,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get messages from a specific session"""
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []
    
    async def archive_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Archive a chat session"""
        try:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                return False
            
            session.is_archived = True
            session.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive session: {e}")
            db.rollback()
            return False
    
    async def delete_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Delete a chat session and all its messages"""
        try:
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                return False
            
            # Delete all messages first (cascade should handle this)
            db.delete(session)
            db.commit()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            db.rollback()
            return False
    
    async def cleanup_old_sessions(
        self,
        db: Session,
        days_old: int = 365
    ) -> int:
        """Clean up old archived sessions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_sessions = db.query(ChatSession).filter(
                ChatSession.is_archived == True,
                ChatSession.updated_at < cutoff_date
            ).all()
            
            count = len(old_sessions)
            
            for session in old_sessions:
                db.delete(session)
            
            db.commit()
            logger.info(f"Cleaned up {count} old sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            db.rollback()
            return 0
    
    async def get_conversation_context(
        self,
        db: Session,
        session_id: uuid.UUID,
        message_limit: int = 10
    ) -> Dict:
        """Get conversation context for AI processing"""
        try:
            messages = await self.get_session_messages(db, session_id, message_limit)
            
            context = {
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "type": msg.message_type
                    }
                    for msg in messages
                ],
                "message_count": len(messages),
                "has_budget_data": any(msg.message_type == "budget_analysis" for msg in messages),
                "has_debt_data": any(msg.message_type == "debt_plan" for msg in messages),
                "has_goals": any(msg.message_type == "goal_plan" for msg in messages)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {"messages": [], "message_count": 0}

# Global instance
chat_history_service = ChatHistoryService()

