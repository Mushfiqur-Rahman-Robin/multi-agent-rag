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
   Copy the example environment file and fill in your keys.
   ```bash
   cp .env.example .env
   ```

3. **Run with Docker**:
   ```bash
   docker compose up --build
   ```

4. **Access the app**:
   Open [http://localhost:8000](http://localhost:8000) in your browser.

## Virtual Environment (Local Development)
If you wish to run outside Docker:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
