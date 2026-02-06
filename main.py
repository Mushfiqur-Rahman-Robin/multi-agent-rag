"""
Main entry point for the Aura Multi-Agent RAG application.

Configures the FastAPI application, initializes middleware, mounts static files,
and sets up the database lifespan management.
"""

import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.multi_agent_rag.api.routes import router
from src.multi_agent_rag.core.config import (
    ALLOWED_ORIGINS,
    APP_HOST,
    APP_PORT,
    APP_RELOAD,
)
from src.multi_agent_rag.core.limiter import limiter
from src.multi_agent_rag.core.logging_config import logger, request_id_var
from src.multi_agent_rag.models.chat import init_db
from src.multi_agent_rag.services.cache_service import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    # Initialize cache service
    await cache_service.initialize()
    # Verify database connection is alive before serving requests
    await init_db()
    yield
    logger.info("Application shutting down...")


app = FastAPI(title="Modular Multi-Agent RAG", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_var.reset(token)


app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/user_upload", StaticFiles(directory="user_upload"), name="user_upload")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=APP_RELOAD)
