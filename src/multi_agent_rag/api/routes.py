"""
API routes for the Aura Multi-Agent RAG system.

Defines endpoints for chat interactions (sync/stream), knowledge base
management (upload/delete), cache auditing, and session history.
"""

import os
import uuid

import aiofiles
import anyio
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.multi_agent_rag.core.config import (
    APPLICATION_API_KEY,
    CHAT_FILE_SIZE_LIMIT,
    KB_FILE_SIZE_LIMIT,
    RATE_LIMIT_PER_MINUTE,
    USER_UPLOAD_FILE_DIR,
    USER_UPLOAD_IMG_DIR,
)
from src.multi_agent_rag.core.limiter import limiter
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.models.chat import AsyncSessionLocal
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.schemas.chat import ChatResponse, Conversation, Message
from src.multi_agent_rag.services.cache_service import cache_service
from src.multi_agent_rag.services.chat_service import ChatService
from src.multi_agent_rag.services.vector_store import vector_store_service

router = APIRouter()

# Security scheme for Swagger UI
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@router.get("/config")
async def get_config():
    """Expose necessary configuration to the frontend."""
    return {"api_key": APPLICATION_API_KEY}


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the application API key for secure communication."""
    if not api_key or api_key != APPLICATION_API_KEY:
        logger.warning("Unauthorized access attempt (missing or invalid API Key)")
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid API Key")
    return api_key


# ==================== Knowledge Base Endpoints ====================


@router.post("/knowledge/upload", dependencies=[Depends(verify_api_key)])
async def upload_knowledge(files: list[UploadFile] = File(...)):
    """
    Upload and index documents into the Knowledge Base.
    """
    results = []
    kb_dir = USER_UPLOAD_FILE_DIR / "kb"
    kb_dir.mkdir(exist_ok=True)

    for file in files:
        # Check file size (10MB)
        content = await file.read()
        if len(content) > KB_FILE_SIZE_LIMIT:
            results.append(
                {
                    "filename": file.filename,
                    "success": False,
                    "error": "File exceeds 10MB limit",
                }
            )
            continue

        file_path = kb_dir / f"kb_{uuid.uuid4()}_{file.filename}"
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(content)

        success = await vector_store_service.ingest_file(str(file_path))
        results.append({"filename": file.filename, "success": success})

    return {"results": results}


@router.get("/knowledge/list", dependencies=[Depends(verify_api_key)])
async def list_knowledge():
    """
    List all documents currently indexed in the Knowledge Base.
    """
    files = await vector_store_service.list_documents()
    return {"files": files}


@router.delete("/knowledge/{filename}", dependencies=[Depends(verify_api_key)])
async def delete_knowledge(filename: str):
    """
    Remove a specific document from the Knowledge Base and its index.
    """
    success = await vector_store_service.delete_document(filename)
    if not success:
        return {"success": False, "message": "File not found or failed to delete"}
    return {"success": True, "message": "Deleted"}


# ==================== Dependencies ====================


async def get_db():
    """Database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session


def get_chat_service(db: AsyncSession = Depends(get_db)):
    """Chat service dependency injection."""
    repo = ChatRepository(db)
    return ChatService(repo)


# ==================== Audit & Stats Endpoints ====================


@router.get("/cache/stats", dependencies=[Depends(verify_api_key)])
async def get_cache_stats(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get cache hit/miss statistics and storage info.
    Also records a snapshot in the database for historical tracking.
    """
    if not cache_service or not cache_service.is_available:
        return {"status": "unavailable", "hits": 0, "misses": 0, "ratio": 0}

    stats = await cache_service.get_stats()

    # Snapshot to DB
    repo = ChatRepository(db)
    await repo.record_cache_stats(stats["hits"], stats["misses"])

    return {"status": "active", **stats}


@router.get("/cache/audit", dependencies=[Depends(verify_api_key)])
async def get_cache_audit(db: AsyncSession = Depends(get_db)):
    """
    Retrieve historical cache audit snapshots from the database.
    """
    repo = ChatRepository(db)
    history = await repo.get_cache_audit_history()
    return {"history": history}


# ==================== Chat & Streaming Endpoints ====================


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request,
    message: str = Form(...),
    thread_id: str | None = Form(None),
    model: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    service: ChatService = Depends(get_chat_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Synchronous chat endpoint. Returns the complete AI response after execution.
    """
    saved_files = []
    if not thread_id:
        thread_id = str(uuid.uuid4())

    if files:
        for file in files:
            content = await file.read()
            if len(content) > CHAT_FILE_SIZE_LIMIT:
                logger.warning(f"File {file.filename} skipped: exceeds 2MB limit")
                continue

            # Determine subdirectory based on mimetype
            sub_dir = (
                USER_UPLOAD_IMG_DIR
                if file.content_type.startswith("image/")
                else USER_UPLOAD_FILE_DIR
            )
            session_dir = sub_dir / thread_id
            session_dir.mkdir(exist_ok=True, parents=True)

            file_path = session_dir / f"{uuid.uuid4()}_{file.filename}"
            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(content)
            saved_files.append(str(file_path))

    t_id, response = await service.run_chat_flow(
        message, thread_id, saved_files, model=model
    )

    # Cleanup temporary files (if UPLOAD_CLEANUP is enabled)
    # Note: We usually keep images if we want to view them later, but here we follow general cleanup
    for f in saved_files:
        try:
            await anyio.to_thread.run_sync(os.remove, f)
        except OSError as e:
            logger.warning(f"Failed to cleanup temp file {f}: {e}")

    return {"thread_id": t_id, "response": response}


@router.post("/chat/stream")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def chat_stream(
    request: Request,
    message: str = Form(...),
    thread_id: str | None = Form(None),
    model: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
    service: ChatService = Depends(get_chat_service),
    api_key: str = Depends(verify_api_key),
):
    """
    Real-time streaming chat endpoint using SSE.
    """
    saved_files = []
    if not thread_id:
        thread_id = str(uuid.uuid4())

    if files:
        for file in files:
            content = await file.read()
            if len(content) > CHAT_FILE_SIZE_LIMIT:
                logger.warning(f"File {file.filename} skipped: exceeds 2MB limit")
                continue

            sub_dir = (
                USER_UPLOAD_IMG_DIR
                if file.content_type.startswith("image/")
                else USER_UPLOAD_FILE_DIR
            )
            session_dir = sub_dir / thread_id
            session_dir.mkdir(exist_ok=True, parents=True)

            file_path = session_dir / f"{uuid.uuid4()}_{file.filename}"
            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(content)
            saved_files.append(str(file_path))

    return StreamingResponse(
        service.stream_chat_flow(message, thread_id, saved_files, model=model),
        media_type="text/event-stream",
    )


# ==================== Session Management Endpoints ====================


@router.get(
    "/sessions",
    response_model=list[Conversation],
    dependencies=[Depends(verify_api_key)],
)
async def list_sessions(service: ChatService = Depends(get_chat_service)):
    """
    Retrieve all conversation threads.
    """
    return await service.get_all_sessions()


@router.get(
    "/sessions/{thread_id}",
    response_model=list[Message],
    dependencies=[Depends(verify_api_key)],
)
async def get_session(thread_id: str, service: ChatService = Depends(get_chat_service)):
    """
    Get the full message history for a specific thread.
    """
    return await service.get_session_history(thread_id)


@router.delete("/sessions/{thread_id}", dependencies=[Depends(verify_api_key)])
async def delete_session(
    thread_id: str, service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation thread and all its history.
    """
    logger.info(f"Deleting session: {thread_id}")
    await service.delete_session(thread_id)
    return {"message": "Deleted"}
