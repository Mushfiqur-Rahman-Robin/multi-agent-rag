from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from src.multi_agent_rag.core.config import SEARCH_MAX_RESULTS, VECTOR_SEARCH_K
from src.multi_agent_rag.core.logging_config import logger


@tool("google_search")
async def google_search(query: str):
    """Search Google for real-time information and news."""
    search = TavilySearchResults(max_results=SEARCH_MAX_RESULTS)
    return await search.ainvoke(query)


@tool("python_repl")
def python_repl(code: str):
    """
    A Python shell. Use this to execute python commands.
    Input should be a valid python command.
    If you expect output it should be printed (e.g. `print(4+4)`).
    """
    try:
        # Using local scope to capture variables
        local_vars = {}
        exec(code, {}, local_vars)  # nosec
        return str(local_vars)
    except Exception as e:
        return f"Error: {e}"


@tool("vector_search")
async def vector_search(query: str, k: int | None = None):
    """
    Search the internal knowledge base for specific documents, facts, or technical details.
    Use this for any project-specific information or uploaded files.
    """
    from src.multi_agent_rag.services.vector_store import vector_store_service

    if k is None:
        k = VECTOR_SEARCH_K
    logger.info(f"Tool Action: Vector Search for query='{query}' k={k}")
    return await vector_store_service.search(query, k=k)
