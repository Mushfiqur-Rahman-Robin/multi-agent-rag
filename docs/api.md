# API Reference

This page provides an overview of the available API endpoints in the Modular Multi-Agent RAG system.

## Authentication

All API endpoints (except `/health`, `/config`, and the root `/`) require authentication via a custom header:

- **Header Name**: `X-API-Key`
- **Value**: Your application API key (available via `/config` or environment variables).

Requests without this header or with an invalid key will return a `403 Forbidden` status code.

## Chat Endpoints


### Post Chat
`POST /chat`
Submits a message to the agentic flow and returns a JSON response.

**Form Data Parameters:**
- `message`: (Required) The text query.
- `thread_id`: (Optional) Existing conversation ID.
- `model`: (Optional) Specific model to use.
- `files`: (Optional) Multiple files/images.

### Stream Chat
`POST /chat/stream`
Streams the agent's thought process and final response using Server-Sent Events (SSE).

## Knowledge Base Endpoints

### Upload Knowledge
`POST /knowledge/upload`
Uploads and indexes documents into the vector store.

### List Documents
`GET /knowledge/list`
Lists all indexed documents.

### Delete Document
`DELETE /knowledge/{filename}`
Removes a specific document and its embeddings.

## Session Management

### List Sessions
`GET /sessions`
Returns a list of all conversation threads with pagination.

**Query Parameters:**
- `limit`: (Optional) Maximum number of sessions to return (default: 50, max: 100).
- `offset`: (Optional) Number of sessions to skip (default: 0).

### Get Session History
`GET /sessions/{thread_id}`
Returns all messages for a specific thread with pagination.

**Query Parameters:**
- `limit`: (Optional) Maximum number of messages to return (default: 50, max: 100).
- `offset`: (Optional) Number of messages to skip (default: 0).

### Delete Session
`DELETE /sessions/{thread_id}`
Deletes a specific thread and its history.

## Cost Management

### List Model Costs
`GET /costs/models`
Returns a summary of total costs, token usage, and request counts for all models used.

### Get Model Cost
`GET /costs/models/{model_name}`
Returns cost details for a specific model.
