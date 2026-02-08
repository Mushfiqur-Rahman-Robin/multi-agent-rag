"""
Chat repository module for the multi-agent RAG system.

Handles all database operations for conversations and messages using SQLAlchemy.
Supports pagination and optimized queries to avoid N+1 problems.
"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.multi_agent_rag.core.config import (
    CACHE_AUDIT_HISTORY_LIMIT,
    DEFAULT_PAGE_SIZE_MESSAGES,
    DEFAULT_PAGE_SIZE_SESSIONS,
    MAX_PAGE_SIZE,
)
from src.multi_agent_rag.models.chat import (
    CacheAudit,
    Conversation,
    Message,
    ModelCostSummary,
)


class ChatRepository:
    """
    Data access layer for conversation and message persistence.
    Supports pagination and optimized queries.
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

    async def get_conversation(self, thread_id: str) -> Conversation | None:
        """
        Retrieve a specific conversation by thread_id.
        """
        stmt = select(Conversation).where(Conversation.thread_id == thread_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_conversation_with_messages(
        self, thread_id: str
    ) -> Conversation | None:
        """
        Retrieve a conversation with its messages eagerly loaded (avoids N+1).
        """
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.thread_id == thread_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_conversations(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Conversation]:
        """
        Retrieve conversations sorted by creation date with pagination.

        Args:
            limit: Maximum number of conversations to return (default from config)
            offset: Number of conversations to skip

        Returns:
            List of conversations
        """
        if limit is None:
            limit = DEFAULT_PAGE_SIZE_SESSIONS
        limit = min(limit, MAX_PAGE_SIZE)

        stmt = (
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_conversations_count(self) -> int:
        """
        Get total count of conversations for pagination metadata.
        """
        stmt = select(func.count(Conversation.id))
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_messages(
        self,
        thread_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Message]:
        """
        Retrieve messages for a specific conversation thread with pagination.

        Args:
            thread_id: The conversation thread ID
            limit: Maximum number of messages to return (default from config)
            offset: Number of messages to skip

        Returns:
            List of messages
        """
        if limit is None:
            limit = DEFAULT_PAGE_SIZE_MESSAGES
        limit = min(limit, MAX_PAGE_SIZE)

        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_messages_count(self, thread_id: str) -> int:
        """
        Get total count of messages for a thread for pagination metadata.
        """
        stmt = select(func.count(Message.id)).where(Message.thread_id == thread_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_recent_messages(
        self, thread_id: str, limit: int = 50
    ) -> list[Message]:
        """
        Retrieve the most recent messages for a thread in ascending order.
        Used for building conversation context.
        """
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(reversed(result.scalars().all()))

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: any,
        model_name: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ):
        """
        Record a new message and update the associated conversation's total cost.
        Also updates the per-model cost summary.
        """
        msg = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )
        self.db.add(msg)

        # Update conversation total cost using UPDATE statement (more efficient)
        if cost > 0:
            await self.db.execute(
                update(Conversation)
                .where(Conversation.thread_id == thread_id)
                .values(total_cost=Conversation.total_cost + cost)
            )

            # Update model cost summary if model is provided
            if model_name:
                await self._update_model_cost_summary(
                    model_name, input_tokens, output_tokens, cost
                )

        await self.db.commit()
        return msg

    async def _update_model_cost_summary(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ):
        """
        Update or create model cost summary record.
        Uses upsert-like logic for atomic updates.
        """
        # Try to get existing record
        stmt = select(ModelCostSummary).where(ModelCostSummary.model_name == model_name)
        result = await self.db.execute(stmt)
        summary = result.scalar_one_or_none()

        if summary:
            # Update existing record
            summary.total_input_tokens += input_tokens
            summary.total_output_tokens += output_tokens
            summary.total_cost += cost
            summary.request_count += 1
        else:
            # Create new record
            summary = ModelCostSummary(
                model_name=model_name,
                total_input_tokens=input_tokens,
                total_output_tokens=output_tokens,
                total_cost=cost,
                request_count=1,
            )
            self.db.add(summary)

    async def get_model_cost_summaries(self) -> list[ModelCostSummary]:
        """
        Retrieve all model cost summaries.
        """
        stmt = select(ModelCostSummary).order_by(ModelCostSummary.total_cost.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_model_cost_summary(self, model_name: str) -> ModelCostSummary | None:
        """
        Retrieve cost summary for a specific model.
        """
        stmt = select(ModelCostSummary).where(ModelCostSummary.model_name == model_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_conversation_title(self, thread_id: str, title: str):
        """
        Update the descriptive title of a conversation.
        Uses UPDATE statement for efficiency.
        """
        await self.db.execute(
            update(Conversation)
            .where(Conversation.thread_id == thread_id)
            .values(title=title)
        )
        await self.db.commit()

    async def update_conversation_cost(self, thread_id: str, cost: float):
        """
        Directly update the total cost for a conversation thread.
        Uses UPDATE statement for efficiency.
        """
        await self.db.execute(
            update(Conversation)
            .where(Conversation.thread_id == thread_id)
            .values(total_cost=Conversation.total_cost + cost)
        )
        await self.db.commit()

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
        audit = CacheAudit(hits=hits, misses=misses)
        self.db.add(audit)
        await self.db.commit()
        return audit

    async def get_cache_audit_history(self, limit: int | None = None) -> list:
        """
        Get historical cache audit snapshots with configurable limit.
        """
        if limit is None:
            limit = CACHE_AUDIT_HISTORY_LIMIT

        stmt = select(CacheAudit).order_by(CacheAudit.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
