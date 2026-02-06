# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-06

### Added
- Comprehensive test suite for chat service, repository, and multimodal utilities.
- Integration tests for API endpoints with security verification.
- API Key authentication documentation in `docs/api.md`.
- Architecture security layer details in `docs/ARCHITECTURE.md`.

### Fixed
- Fixed `AttributeError` in `ChatRepository` unit tests related to async mocking.
- Fixed `AssertionError` in `ChatService` unit tests by properly matching keyword arguments in `add_message`.
- Fixed `403 Forbidden` errors in integration tests by implementing proper `X-API-Key` header handling.
- Installed missing `redis` dependency in the virtual environment.

### Security
- Implemented mandatory `X-API-Key` header verification for all business-critical API endpoints.
