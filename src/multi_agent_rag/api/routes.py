from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.multi_agent_rag.models.chat import AsyncSessionLocal
from src.multi_agent_rag.repositories.chat_repository import ChatRepository
from src.multi_agent_rag.services.chat_service import ChatService
from src.multi_agent_rag.schemas.chat import Conversation, Message, ChatResponse
from src.multi_agent_rag.core.config import UPLOAD_DIR
from src.multi_agent_rag.core.logging_config import logger
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from fastapi.responses import FileResponse, StreamingResponse
import os

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def get_chat_service(db: AsyncSession = Depends(get_db)):
    repo = ChatRepository(db)
    return ChatService(repo)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    thread_id: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    service: ChatService = Depends(get_chat_service)
):
    saved_files = []
    if files:
        for file in files:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))

    t_id, response = await service.run_chat_flow(message, thread_id, saved_files, model=model)
    
    # Cleanup
    import os
    for f in saved_files:
        try: os.remove(f)
        except: pass

    return {"thread_id": t_id, "response": response}

@router.post("/chat/stream")
async def chat_stream(
    message: str = Form(...),
    thread_id: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    service: ChatService = Depends(get_chat_service)
):
    saved_files = []
    if files:
        for file in files:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))

    return StreamingResponse(
        service.stream_chat_flow(message, thread_id, saved_files, model=model),
        media_type="text/event-stream"
    )

@router.get("/sessions", response_model=List[Conversation])
async def list_sessions(service: ChatService = Depends(get_chat_service)):
    return await service.get_all_sessions()

@router.get("/sessions/{thread_id}", response_model=List[Message])
async def get_session(thread_id: str, service: ChatService = Depends(get_chat_service)):
    return await service.get_session_history(thread_id)

@router.delete("/sessions/{thread_id}")
async def delete_session(thread_id: str, service: ChatService = Depends(get_chat_service)):
    logger.info(f"Deleting session: {thread_id}")
    await service.delete_session(thread_id)
    return {"message": "Deleted"}
