# Setup Guide

## Prerequisites
- Docker & Docker Compose
- OpenAI API Key
- Tavily API Key

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd multi-agent-rag
   ```

2. **Configure Environment**:
   Aura uses an environment-aware configuration system. Create a file based on your branch:
   - **Local/Dev**: `.env.dev`
   - **Staging**: `.env.staging`
   - **Production**: `.env.prod`

   ```bash
   cp .env.example .env.dev
   ```
   *Note: If no specific file is found, it will fallback to `.env`.*

3. **Run with Docker**:
   ```bash
   docker compose up --build
   ```

4. **Access the app**:
   Open [http://localhost:8777](http://localhost:8777) in your browser.

## Virtual Environment (Local Development)

If you wish to run locally:

1. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

2. **Activate the environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Set your API Key**:
   Ensure `APPLICATION_API_KEY` is set in your `.env` file. You will need this for all API requests.

4. **Run the application**:
   ```bash
   python main.py
   ```

## Running Tests
To ensure everything is working correctly:
```bash
source .venv/bin/activate
pytest
```
