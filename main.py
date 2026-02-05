from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.multi_agent_rag.api.routes import router
from src.multi_agent_rag.models.chat import init_db
from src.multi_agent_rag.core.config import APP_HOST, APP_PORT, APP_RELOAD
from src.multi_agent_rag.core.logging_config import logger
import uvicorn

app = FastAPI(title="Modular Multi-Agent RAG")

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    logger.info("Application starting up...")
    # Verify database connection is alive before serving requests
    await init_db()

if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=APP_RELOAD)
