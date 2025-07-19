from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import ConversationLog

async def log_conversation(db: AsyncSession, session_id: str, user_transcript: str, bot_response: str, intent: str, emotion: str, escalate: bool):
    log = ConversationLog(
        session_id=session_id,
        user_transcript=user_transcript,
        bot_response=bot_response,
        intent=intent,
        emotion=emotion,
        escalate=escalate
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
