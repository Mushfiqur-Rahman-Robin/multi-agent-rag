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

### 4. Caching & Performance (Redis Stack)
- **Redis Stack**: Orchestrates multiple caching tiers to reduce latency and API costs.
- **Research Cache**: Stores research reports to skip redundant web searches.
- **Response Cache**: Uses request context hashing (message + history + files) for instant response retrieval.
- **Vector Cache**: Optimizes repeated semantic search queries.

### 5. File Storage Strategy
- **User Uploads**: Mounted volumes at `/app/user_upload` and `/app/uploads` persist user files natively.
- **Static Hosting**: Files are served directly via FastAPI static mounts.
- **Message Linking**: URLs are stored in JSON message content in Postgres.

### 6. Interactive Frontend (Vanilla JS + CSS)
- **Responsive Design**: Premium dark-mode interface optimized for high-resolution displays.
- **Real-time Feedback**: Streams agent "thoughts" and intermediate plans via SSE.

## 🔄 Interaction Flow

1. **User Query**: The user sends a request through the frontend.
2. **Intent Routing**: The Router agent evaluates whether to go to Research, Planning, or Implementation.
3. **Agent Execution**: Selected agents gather data, plan, and code.
4. **Final Synthesis**: The Responder agent produces a polished output including implementation code.

## 🛡️ Security & CI/CD
- **API Security**: `X-API-Key` mandatory verification for all sensitive endpoints.
- **Automated CI**: GitHub Actions (Pytest, Ruff, Bandit, Detect-secrets) on every push.
- **Deployment**: Branch-aware SSH deployment to remote servers using GitHub Actions.
- **Non-Root Execution**: Optimized Docker security running as `appuser`.
- **Environment Isolation**: Distinct `.env.dev`, `.env.staging`, and `.env.prod` configurations.
