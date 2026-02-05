from langchain_openai import ChatOpenAI
from src.multi_agent_rag.core.config import DEFAULT_MODEL, OPENAI_API_KEY
from langchain_core.messages import SystemMessage
import json

from src.multi_agent_rag.core.logging_config import logger

def router_node(state):
    logger.info("Router node evaluating intent.")
    selected_model = state.get("model") or DEFAULT_MODEL
    llm = ChatOpenAI(model=selected_model, openai_api_key=OPENAI_API_KEY)
    
    last_message = state["messages"][-1].content if state["messages"] else ""
    
    # State context
    has_research = bool(state.get("research_output"))
    has_plan = bool(state.get("plan"))
    has_code = bool(state.get("code"))
    
    prompt = f"""Analyze the user's message and the current status of the task to decide the next step.

    Status:
    - Research Gathered: {has_research}
    - Strategic Plan Created: {has_plan}
    - Code Implemented: {has_code}

    User Message: "{last_message}"
    
    Decision Rules:
    1. If the user wants to gather information, search the web, or if the request is complex and no research has been done yet, return 'research'.
    2. If research is done but no plan exists, and the user wants to proceed or asks "how" to do it, return 'plan'.
    3. If a plan exists and the user wants to implement it, write code, or execute the steps, return 'code'.
    4. If the user is giving feedback on a specific stage (e.g., "change the plan", "add more research"), return that stage's name ('research', 'plan', or 'code').
    5. If it's a simple greeting, general question, or doesn't fit the above, return 'respond'.

    Return ONLY one word: 'research', 'plan', 'code', or 'respond'."""
    
    response = llm.invoke([SystemMessage(content=prompt)])
    decision = response.content.strip().lower()
    
    # Clean up decision
    if "research" in decision:
        state["next_step"] = "research"
        state["thought"] = "User request requires information lookup or research update."
    elif "plan" in decision:
        state["next_step"] = "plan"
        state["thought"] = "Moving to planning stage based on research context."
    elif "code" in decision:
        state["next_step"] = "code"
        state["thought"] = "Proceeding to implementation/coding stage."
    else:
        state["next_step"] = "respond"
        state["thought"] = "Handling as a direct conversational response."
        
    logger.info(f"Router decision: {state['next_step']} - Thought: {state['thought']}")
    return state

def direct_responder(state):
    logger.info("Direct responder activated.")
    selected_model = state.get("model") or DEFAULT_MODEL
    llm = ChatOpenAI(model=selected_model, openai_api_key=OPENAI_API_KEY)
    
    messages = [
        SystemMessage(content="You are a helpful assistant. Provide a direct, concise response to the user's inquiry.")
    ] + state["messages"]
    
    response = llm.invoke(messages)
    state["final_response"] = response.content
    state["thought"] = "Generated a direct response."
    
    return {"messages": [response], "final_response": state["final_response"], "thought": state["thought"]}
