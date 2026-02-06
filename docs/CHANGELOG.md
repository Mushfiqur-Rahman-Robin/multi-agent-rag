# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-06

### Added
- Comprehensive test suite for chat service, repository, and multimodal utilities.
- Integration tests for API endpoints with security verification.
- API Key authentication documentation in `docs/api.md`.
- Architecture security layer details in `docs/ARCHITECTURE.md`.
- `aiofiles` dependency for non-blocking file I/O.
- **File Persistence**: Implemented durable file storage for chat attachments.
  - Mounts `/user_upload` for direct file serving.
  - Persists file URLs in conversation history.
  - Enhanced UI to render PDFs and files natively in the chat history.
- **Content Extraction**: Added backend support to extract text from PDF and DOCX files for LLM context inclusion.

### Changed
- **Async/Await Optimization**: Audited the entire codebase for correct asynchronous usage.
  - Refactored `CacheService` to use `redis.asyncio` for non-blocking Redis operations.
  - Updated `VectorStoreService` to offload blocking LangChain and ChromaDB operations to worker threads using `anyio`.
  - Converted `create_multimodal_message` and `encode_image` to asynchronous functions using `aiofiles`.
  - Replaced blocking file I/O in API routes with asynchronous `aiofiles` operations.
  - **Fixed Tools Protocol**: Converted `google_search` and `vector_search` tools to asynchronous (`async def`) to correctly await service calls, fixing the issue where Knowledge Base results were returning coroutine objects instead of data.
  - **Structured Storage & Limits**: Implemented strict file size limits and organized storage.
    - Added user-facing alerts for file size limits (2MB for chat, 10MB for Knowledge Base).
    - Structured `user_upload` directory into `img/` and `file/` subfolders, organized by session (thread) ID.
    - Added backend validation for file sizes in both sync and stream chat endpoints.
  - Initialized `CacheService` within the FastAPI lifespan for proper resource management.

### Fixed
- Fixed `AttributeError` in `ChatRepository` unit tests related to async mocking.
- Fixed `AssertionError` in `ChatService` unit tests by properly matching keyword arguments in `add_message`.
- Fixed `403 Forbidden` errors in integration tests by implementing proper `X-API-Key` header handling.
- **Security**: Fixed `bandit` B110 issues in `CacheService` by replacing empty `except: pass` blocks with debug logging.
- Installed missing `redis` dependency in the virtual environment.

### Security
- Implemented mandatory `X-API-Key` header verification for all business-critical API endpoints.
