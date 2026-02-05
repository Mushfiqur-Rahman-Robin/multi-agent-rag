from langchain_openai import ChatOpenAI
from src.multi_agent_rag.core.config import SEARCH_MODEL, OPENAI_API_KEY
from src.multi_agent_rag.core.tools import google_search
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

def research_agent(state):
    logger.info("Research agent initiated.")
    llm = ChatOpenAI(model=SEARCH_MODEL, openai_api_key=OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([google_search])
    
    messages = [
        SystemMessage(content="You are a professional research agent. Your goal is to search the internet to gather comprehensive information about the user's request. Use the search tool to find relevant facts, data, and insights.")
    ] + state["messages"]
    
    # In a real LangGraph implementation, we might use a ToolNode.
    # For simplicity here, we'll demonstrate a simplified node logic.
    response = llm_with_tools.invoke(messages)
    
    new_messages = [response]
    
    # Handle tool calls if any
    if response.tool_calls:
        state["thought"] = "Complex research required. Using internet search tools."
        for tool_call in response.tool_calls:
            if tool_call["name"] == "google_search":
                search_results = google_search.invoke(tool_call["args"])
                # Create a ToolMessage to satisfy OpenAI requirements
                new_messages.append(ToolMessage(
                    content=str(search_results),
                    tool_call_id=tool_call["id"]
                ))
                state["research_output"] = str(search_results)
    else:
        state["research_output"] = response.content
        state["thought"] = "Information found without external tools."
    
    state["final_response"] = "I have completed the research phase. You can review the findings below. Would you like me to create a strategic plan based on this, or do you have more questions?"
        
    return {"messages": new_messages, "research_output": state["research_output"], "thought": state["thought"], "final_response": state["final_response"]}
