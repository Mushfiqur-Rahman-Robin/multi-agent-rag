from langchain_google_genai import ChatGoogleGenerativeAI
from src.multi_agent_rag.core.config import CODER_MODEL, GEMINI_API_KEY
from src.multi_agent_rag.core.tools import python_repl
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import SystemMessage

def coding_agent(state):
    llm = ChatGoogleGenerativeAI(model=CODER_MODEL, google_api_key=GEMINI_API_KEY)
    llm_with_tools = llm.bind_tools([python_repl])
    
    plan_context = state.get("plan", "No plan available.")
    research_context = state.get("research_output", "")
    
    messages = [
        SystemMessage(content=f"You are an expert coding agent. Your goal is to implement the steps outlined in the provided plan. Use the research data as context. If the plan requires calculations or data processing, use the python_repl tool.\n\nPlan:\n{plan_context}\n\nResearch Context:\n{research_context}")
    ] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    # Handle tool calls for python_repl if any
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "python_repl":
                execution_result = python_repl.invoke(tool_call["args"])
                # Normally we'd feed this back, but for MVP we'll just store and finish
                state["code"] = execution_result
    else:
        state["code"] = response.content
        
    return {"messages": [response], "code": state["code"]}
