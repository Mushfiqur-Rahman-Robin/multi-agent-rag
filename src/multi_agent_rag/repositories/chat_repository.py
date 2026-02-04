from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.multi_agent_rag.models.chat import Conversation, Message
from typing import List, Optional

class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(self, thread_id: str, title: str):
        new_conv = Conversation(thread_id=thread_id, title=title)
        self.db.add(new_conv)
        await self.db.commit()
        return new_conv

    async def get_conversations(self) -> List[Conversation]:
        stmt = select(Conversation).order_by(Conversation.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_messages(self, thread_id: str) -> List[Message]:
        stmt = select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.asc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def add_message(self, thread_id: str, role: str, content: any):
        msg = Message(thread_id=thread_id, role=role, content=content)
        self.db.add(msg)
        await self.db.commit()
        return msg

    async def delete_conversation(self, thread_id: str):
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            await self.db.delete(conv)
            await self.db.commit()
