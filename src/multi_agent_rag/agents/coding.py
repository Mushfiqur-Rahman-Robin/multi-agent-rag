from langchain_openai import ChatOpenAI
from src.multi_agent_rag.core.config import CODER_MODEL, OPENAI_API_KEY
from src.multi_agent_rag.core.tools import python_repl
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import SystemMessage, ToolMessage

def coding_agent(state):
    logger.info("Coding agent initiated.")
    llm = ChatOpenAI(model=CODER_MODEL, openai_api_key=OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([python_repl])
    
    plan_context = state.get("plan", "No plan available.")
    research_context = state.get("research_output", "")
    
    messages = [
        SystemMessage(content=f"You are an expert coding agent. Your goal is to implement the steps outlined in the provided plan. Use the research data as context. If the plan requires calculations or data processing, use the python_repl tool.\n\nPlan:\n{plan_context}\n\nResearch Context:\n{research_context}")
    ] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    new_messages = [response]
    
    # Handle tool calls for python_repl if any
    if response.tool_calls:
        state["thought"] += f"\nExecuting code via python_repl: {len(response.tool_calls)} calls."
        for tool_call in response.tool_calls:
            if tool_call["name"] == "python_repl":
                execution_result = python_repl.invoke(tool_call["args"])
                new_messages.append(ToolMessage(
                    content=str(execution_result),
                    tool_call_id=tool_call["id"]
                ))
                state["code"] = execution_result
    else:
        state["code"] = response.content
        state["thought"] += "\nGenerated code/response directly."
    
    state["final_response"] = "The implementation is ready. You can see the code output below. Let me know if you need any adjustments or further explanations!"
        
    return {"messages": new_messages, "code": state["code"], "thought": state["thought"], "final_response": state["final_response"]}
