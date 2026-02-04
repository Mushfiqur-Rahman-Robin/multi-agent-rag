# Lean Multi-Agent RAG System

This repository contains a lean, multimodal, multi-agent RAG system powered by Gemini 2.0 Flash and LangGraph.

## Architecture

The system consists of three specialized agents:
1.  **Research Agent**: Uses Tavily/Google Search to gather information from the internet.
2.  **Planning Agent**: Drafts a detailed plan based on the research findings.
3.  **Coding Agent**: Implements the plan, with access to a Python interpreter for verification.

## Features
- **Visual Interface**: Premium ChatGPT-like web UI with a dark-mode theme.
- **Multimodal Support**: Handles Text, Image, and Voice inputs.
- **Session Management**: Persistent conversation threads stored in PostgreSQL.
- **Lean Codebase**: Optimized for performance and simplicity, no local models required.
- **State-of-the-Art Models**: Uses Gemini 2.5 Flash for fast and capable reasoning.

## Requirements
- `GEMINI_API_KEY`
- `TAVILY_API_KEY` (Optional)
- `DATABASE_URL` (Handled by Docker)

## Getting Started

### Using Docker
1. Create a `.env` file with your API keys.
2. Run:
   ```bash
   docker-compose up --build
   ```

### Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python main.py
   ```

## API Documentation

### Chat with Session
`POST /chat`
- `message`: (string, Form) The user's query.
- `thread_id`: (string, Optional, Form) ID for continuing a conversation.
- `files`: (file, Optional) Multimodal inputs (images/audio).

### Session Management
- `GET /sessions`: List all conversation threads.
- `GET /sessions/{thread_id}`: Get full message history for a specific thread.
- `DELETE /sessions/{thread_id}`: Delete a conversation thread.

---
Created by Antigravity.