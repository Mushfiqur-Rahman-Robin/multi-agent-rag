from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: Any

class MessageCreate(MessageBase):
    thread_id: str

class Message(MessageBase):
    id: int
    thread_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConversationBase(BaseModel):
    thread_id: str
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    thread_id: str
    response: Any
