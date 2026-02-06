from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


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
    title: str | None = None


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    thread_id: str
    response: Any
