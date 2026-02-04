from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
import os

@tool
def google_search(query: str):
    """Search the internet for information."""
    search = TavilySearchResults(max_results=5)
    return search.invoke(query)

@tool
def python_repl(code: str):
    """Execute python code and return the result. Use this to verify code or perform calculations."""
    try:
        # Warning: Using exec() is generally unsafe in production without sandboxing.
        # But for this task, we'll assume a controlled environment.
        # Use a local dict for variables
        local_vars = {}
        exec(code, {}, local_vars)
        return str(local_vars)
    except Exception as e:
        return f"Error executing code: {str(e)}"

# More tools can be added here
