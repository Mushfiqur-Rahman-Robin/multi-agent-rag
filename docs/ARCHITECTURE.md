# Aura - Multi-Agent RAG System Architecture

Aura is a sophisticated multi-agent system designed for research, planning, and implementation of complex technical queries. It utilizes LangGraph to coordinate specialized agents in a human-in-the-loop interactive flow.

## 🏗️ Core Architecture

The system is built on a modular architecture with the following main pillars:

### 1. Multi-Agent Orchestration (LangGraph)
Aura uses a stateful computational graph where nodes represent specialized agents and edges define the workflow transitions.

- **Router**: Analyzes user intent and conversation history to decide which agent to engage next.
- **Researcher**: Uses Tavily and Google Search tools to gather real-time internet data.
- **Planner**: Drafts structured technical roadmaps based on research output.
- **Coder**: Implements specific modules or runs simulations using a Python REPL environment.

### 2. API & Backend (FastAPI)
- **FastAPI**: Provides a high-performance asynchronous interface.
- **Service Layer**: Decouples API routes from business logic (multimodal processing, graph execution).
- **Repositories**: Abstracts database interactions using SQLAlchemy.

### 3. Database & Persistance (PostgreSQL)
- Stores conversations and multimodal messages.
- Uses Alembic for schema migrations.
- Implements a thread-based history mechanism for the agents to maintain context.

### 4. Interactive Frontend (Vanilla JS + CSS)
- **Responsive Design**: Premium dark-mode interface.
- **Real-time Feedback**: Visualises agent "thoughts" and intermediate steps (plans, code outputs).
- **Multimodal Support**: Handles file uploads (images/audio) for cross-modal reasoning.

## 🔄 Interaction Flow

1. **User Query**: The user sends a request through the frontend.
2. **Intent Routing**: The Router agent evaluates whether to go to Research, Planning, or Implementation based on current state.
3. **Agent Execution**: The selected agent performs its task and returns a human-readable summary.
4. **Human Feedback**: The system stops and waits for user confirmation or further instructions, enabling iterative refinement.

## 🛡️ Security & Performance
- **API Security**: Implements `X-API-Key` mandatory header verification for all business-critical endpoints.
- **Non-Root Execution**: Runs as a non-root user in Docker to minimize attack surface.
- **Optimized Builds**: Multi-stage Docker builds for minimal image size.
- **Reliability**: Connection pooling and exponential backoff retry logic for database and LLM calls.
