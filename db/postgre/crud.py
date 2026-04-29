from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, asc, func
from db.postgre import models
import uuid

async def create_conversation(db: AsyncSession, user_id: str, title: str = "New Conversation") -> models.Conversation:
    db_conversation = models.Conversation(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title
    )

    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)

    return db_conversation

async def save_message(db: AsyncSession, conversation_id: uuid.UUID, role: str, content: str, sources: list = None, tool_calls: list = None) -> models.Message:
    db_message = models.Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources,
        tool_calls=tool_calls
    )
    db.add(db_message)
    
    result = await db.execute(select(models.Conversation).filter(models.Conversation.id == conversation_id))
    conversation = result.scalars().first()

    if conversation:
        conversation.updated_at = func.now()

    await db.commit()
    await db.refresh(db_message)

    return db_message

async def get_chat_history(db: AsyncSession, conversation_id: uuid.UUID, limit: int = 10):
    stmt = (
        select(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(asc(models.Message.created_at))
        .limit(limit)
    )
    
    result = await db.execute(stmt)

    return result.scalars().all()

async def get_conversations_by_user(db: AsyncSession, user_id: str = None, limit: int = 20):
    stmt = select(models.Conversation)
    if user_id:
        stmt = stmt.filter(models.Conversation.user_id == user_id)
        
    stmt = stmt.order_by(desc(models.Conversation.updated_at)).limit(limit)
    result = await db.execute(stmt)

    return result.scalars().all()

async def delete_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(models.Conversation).filter(models.Conversation.id == conversation_id)
    )
    db_conversation = result.scalars().first()
    
    if db_conversation:
        await db.delete(db_conversation)
        await db.commit()
        return True
        
    return False


async def update_conversation_title(db: AsyncSession, conversation_id: uuid.UUID, title: str):
    result = await db.execute(
        select(models.Conversation).filter(models.Conversation.id == conversation_id)
    )
    db_conversation = result.scalars().first()

    if not db_conversation:
        return None

    db_conversation.title = title
    await db.commit()
    await db.refresh(db_conversation)

    return db_conversation
