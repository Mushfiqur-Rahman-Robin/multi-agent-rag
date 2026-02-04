import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from src.multi_agent_rag.core.config import DATABASE_URL, DB_MAX_RETRIES, DB_RETRY_DELAY
from src.multi_agent_rag.core.logging_config import logger

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, ForeignKey("conversations.thread_id", ondelete="CASCADE"), index=True)
    role = Column(String)  # 'human', 'ai'
    content = Column(JSON) # Stores multimodal content or text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")

async def init_db():
    """Attempt to connect to the database with retries."""
    for attempt in range(1, DB_MAX_RETRIES + 1):
        try:
            logger.info(f"Database connection attempt {attempt}/{DB_MAX_RETRIES}...")
            async with engine.begin() as conn:
                # This doesn't create tables anymore (Alembic does), 
                # but it verifies the connection is alive.
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
