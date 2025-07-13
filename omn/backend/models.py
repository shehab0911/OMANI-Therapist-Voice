from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_transcript = Column(Text)
    bot_response = Column(Text)
    intent = Column(String)
    emotion = Column(String)
    escalate = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
