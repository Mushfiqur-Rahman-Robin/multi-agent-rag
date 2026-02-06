# API Reference

This page provides an overview of the available API endpoints in the Modular Multi-Agent RAG system.

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
Returns a list of all conversation threads.

### Get Session History
`GET /sessions/{thread_id}`
Returns all messages for a specific thread.

### Delete Session
`DELETE /sessions/{thread_id}`
Deletes a specific thread and its history.
