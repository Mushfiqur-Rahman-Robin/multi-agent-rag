"""
API routes for the Aura Multi-Agent RAG system.

Defines endpoints for chat interactions (sync/stream), knowledge base
management (upload/delete), cache auditing, and session history.
"""

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.multi_agent_rag.core.config import UPLOAD_DIR
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.models.chat import AsyncSessionLocal
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.schemas.chat import ChatResponse, Conversation, Message
from src.multi_agent_rag.services.cache_service import cache_service
from src.multi_agent_rag.services.chat_service import ChatService
from src.multi_agent_rag.services.vector_store import vector_store_service

router = APIRouter()

# ==================== Knowledge Base Endpoints ====================


@router.post("/knowledge/upload")
async def upload_knowledge(files: list[UploadFile] = File(...)):
    """
    Upload and index documents into the Knowledge Base.
    """
    results = []
    for file in files:
        file_path = UPLOAD_DIR / f"kb_{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        success = await vector_store_service.ingest_file(str(file_path))
        results.append({"filename": file.filename, "success": success})

    return {"results": results}


@router.get("/knowledge/list")
async def list_knowledge():
    """
    List all documents currently indexed in the Knowledge Base.
    """
    files = await vector_store_service.list_documents()
    return {"files": files}


@router.delete("/knowledge/{filename}")
async def delete_knowledge(filename: str):
    """
    Remove a specific document from the Knowledge Base and its index.
    """
    success = await vector_store_service.delete_document(filename)
    if not success:
        return {"success": False, "message": "File not found or failed to delete"}
    return {"success": True, "message": "Deleted"}


# ==================== Audit & Stats Endpoints ====================


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache hit/miss statistics and storage info.
    """
    if not cache_service or not cache_service.is_available:
        return {"status": "unavailable", "hits": 0, "misses": 0, "ratio": 0}

    stats = cache_service.get_stats()
    return {"status": "active", **stats}


# ==================== Dependencies ====================


async def get_db():
    """Database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session


def get_chat_service(db: AsyncSession = Depends(get_db)):
    """Chat service dependency injection."""
    repo = ChatRepository(db)
    return ChatService(repo)


# ==================== Chat & Streaming Endpoints ====================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    thread_id: str | None = Form(None),
    model: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    service: ChatService = Depends(get_chat_service),
):
    """
    Synchronous chat endpoint. Returns the complete AI response after execution.
    """
    saved_files = []
    if files:
        for file in files:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))

    t_id, response = await service.run_chat_flow(
        message, thread_id, saved_files, model=model
    )

    # Cleanup temporary files
    for f in saved_files:
        try:
            os.remove(f)
        except OSError as e:
            logger.warning(f"Failed to cleanup temp file {f}: {e}")

    return {"thread_id": t_id, "response": response}


@router.post("/chat/stream")
async def chat_stream(
    message: str = Form(...),
    thread_id: str | None = Form(None),
    model: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    service: ChatService = Depends(get_chat_service),
):
    """
    Real-time streaming chat endpoint using SSE.
    """
    saved_files = []
    if files:
        for file in files:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))

    return StreamingResponse(
        service.stream_chat_flow(message, thread_id, saved_files, model=model),
        media_type="text/event-stream",
    )


# ==================== Session Management Endpoints ====================


@router.get("/sessions", response_model=list[Conversation])
async def list_sessions(service: ChatService = Depends(get_chat_service)):
    """
    Retrieve all conversation threads.
    """
    return await service.get_all_sessions()


@router.get("/sessions/{thread_id}", response_model=list[Message])
async def get_session(thread_id: str, service: ChatService = Depends(get_chat_service)):
    """
    Get the full message history for a specific thread.
    """
    return await service.get_session_history(thread_id)


@router.delete("/sessions/{thread_id}")
async def delete_session(
    thread_id: str, service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation thread and all its history.
    """
    logger.info(f"Deleting session: {thread_id}")
    await service.delete_session(thread_id)
    return {"message": "Deleted"}
