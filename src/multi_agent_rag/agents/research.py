from langchain_google_genai import ChatGoogleGenerativeAI
from src.multi_agent_rag.core.config import SEARCH_MODEL, GEMINI_API_KEY
from src.multi_agent_rag.core.tools import google_search
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import HumanMessage, SystemMessage

def research_agent(state):
    llm = ChatGoogleGenerativeAI(model=SEARCH_MODEL, google_api_key=GEMINI_API_KEY)
    llm_with_tools = llm.bind_tools([google_search])
    
    messages = [
        SystemMessage(content="You are a professional research agent. Your goal is to search the internet to gather comprehensive information about the user's request. Use the search tool to find relevant facts, data, and insights.")
    ] + state["messages"]
    
    # In a real LangGraph implementation, we might use a ToolNode.
    # For simplicity here, we'll demonstrate a simplified node logic.
    logger.info("Research agent initiated.")
    response = llm_with_tools.invoke(messages)
    
    # Handle tool calls if any
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "google_search":
                search_results = google_search.invoke(tool_call["args"])
                # Add tool results back to the conversation
                # (This is a simplified version of the LangGraph loop)
                state["research_output"] = str(search_results)
    else:
        state["research_output"] = response.content
        
    return {"messages": [response], "research_output": state["research_output"]}
