"""
Database models and initialization module for the Aura Multi-Agent RAG system.

Defines SQLAlchemy ORM models for conversations and messages, and provides
the database engine initialization with retry logic.
"""

import asyncio

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from src.multi_agent_rag.core.config import DATABASE_URL, DB_MAX_RETRIES, DB_RETRY_DELAY
from src.multi_agent_rag.core.logging_config import logger

# Initialize Async SQLAlchemy Engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Conversation(Base):
    """
    Model representing a unique conversation session or thread.
    """

    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Cascade delete messages when a conversation is removed
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """
    Model representing an individual message within a conversation.
    """

    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(
        String, ForeignKey("conversations.thread_id", ondelete="CASCADE"), index=True
    )
    role = Column(String)  # 'human', 'ai'
    content = Column(
        JSON
    )  # Structured payload containing text, thoughts, research, etc.
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class CacheAudit(Base):
    """
    Model for tracking periodic snapshots of cache performance stats.
    """

    __tablename__ = "cache_audit"
    id = Column(Integer, primary_key=True, index=True)
    hits = Column(Integer, default=0, nullable=False)
    misses = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def init_db():
    """
    Attempt to initialize and verify the database connection with retries.
    Uses exponential-backoff logic defined in configuration.
    """
    for attempt in range(1, DB_MAX_RETRIES + 1):
        try:
            logger.info(f"Database connection attempt {attempt}/{DB_MAX_RETRIES}...")
            async with engine.begin() as conn:
                # Basic health check query
                await conn.execute(func.now())
            logger.info("Database connection established successfully.")
            return
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            if attempt == DB_MAX_RETRIES:
                logger.critical("Final database connection attempt failed. Exiting.")
                raise e
            logger.info(f"Retrying in {DB_RETRY_DELAY} seconds...")
            await asyncio.sleep(DB_RETRY_DELAY)
