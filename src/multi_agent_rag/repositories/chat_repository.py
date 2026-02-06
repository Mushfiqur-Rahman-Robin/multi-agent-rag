"""
Chat repository module for the multi-agent RAG system.

Handles all database operations for conversations and messages using SQLAlchemy.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.multi_agent_rag.models.chat import Conversation, Message


class ChatRepository:
    """
    Data access layer for conversation and message persistence.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the repository with a database session.
        """
        self.db = db

    async def create_conversation(self, thread_id: str, title: str):
        """
        Create a new conversation record.
        """
        new_conv = Conversation(thread_id=thread_id, title=title)
        self.db.add(new_conv)
        await self.db.commit()
        return new_conv

    async def get_conversations(self) -> list[Conversation]:
        """
        Retrieve all conversations sorted by creation date.
        """
        stmt = select(Conversation).order_by(Conversation.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_messages(self, thread_id: str) -> list[Message]:
        """
        Retrieve all messages for a specific conversation thread.
        """
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: any,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ):
        """
        Record a new message and update the associated conversation's total cost.
        """
        msg = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        self.db.add(msg)

        # Update conversation total cost
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.total_cost = (conv.total_cost or 0.0) + cost

        await self.db.commit()
        return msg

    async def update_conversation_title(self, thread_id: str, title: str):
        """
        Update the descriptive title of a conversation.
        """
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.title = title
            await self.db.commit()
        return conv

    async def update_conversation_cost(self, thread_id: str, cost: float):
        """
        Directly update the total cost for a conversation thread.
        """
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.total_cost = (conv.total_cost or 0.0) + cost
            await self.db.commit()
        return conv

    async def delete_conversation(self, thread_id: str):
        """
        Delete a conversation and all its cascading messages.
        """
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            await self.db.delete(conv)
            await self.db.commit()

    async def record_cache_stats(self, hits: int, misses: int):
        """
        Record a snapshot of the current cache hit/miss stats.
        """
        from src.multi_agent_rag.models.chat import CacheAudit

        audit = CacheAudit(hits=hits, misses=misses)
        self.db.add(audit)
        await self.db.commit()
        return audit

    async def get_cache_audit_history(self, limit: int = 100) -> list:
        """
        Get historical cache audit snapshots.
        """
        from src.multi_agent_rag.models.chat import CacheAudit

        stmt = select(CacheAudit).order_by(CacheAudit.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
