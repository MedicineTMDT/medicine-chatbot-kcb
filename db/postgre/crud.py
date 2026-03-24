from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from db.postgre import models
import uuid

def create_conversation(db: Session, user_id: str = None, title: str = "New Conversation") -> models.Conversation:
    db_conversation = models.Conversation(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def save_message(db: Session, conversation_id: uuid.UUID, role: str, content: str) -> models.Message:
    db_message = models.Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(db_message)
    
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = db_message.created_at

    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, conversation_id: uuid.UUID, limit: int = 10):
    messages = db.query(models.Message)\
                 .filter(models.Message.conversation_id == conversation_id)\
                 .order_by(asc(models.Message.created_at))\
                 .limit(limit)\
                 .all()
    return messages

def get_conversations_by_user(db: Session, user_id: str = None, limit: int = 20):
    query = db.query(models.Conversation)
    if user_id:
        query = query.filter(models.Conversation.user_id == user_id)
        
    return query.order_by(desc(models.Conversation.updated_at)).limit(limit).all()

def delete_conversation(db: Session, conversation_id: uuid.UUID) -> bool:
    db_conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
        return True
        
    return False