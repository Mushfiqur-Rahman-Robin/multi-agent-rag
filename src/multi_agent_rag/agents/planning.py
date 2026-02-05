from langchain_openai import ChatOpenAI
from src.multi_agent_rag.core.config import PLANNER_MODEL, OPENAI_API_KEY
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import SystemMessage

def planning_agent(state):
    logger.info("Planning agent initiated.")
    llm = ChatOpenAI(model=PLANNER_MODEL, openai_api_key=OPENAI_API_KEY)
    
    research_context = state.get("research_output", "No research data available.")
    
    messages = [
        SystemMessage(content=f"You are a strategic planning agent. Based on the following research data, create a detailed step-by-step plan/draft for the final output. The plan should be structured and serve as a roadmap for the coding agent.\n\nResearch Data:\n{research_context}")
    ] + state["messages"]
    
    response = llm.invoke(messages)
    state["plan"] = response.content
    state["thought"] += "\nStrategic plan drafted based on research."
    state["final_response"] = "I've drafted a step-by-step plan for your request. Please review it. If it looks good, I can proceed with the implementation, or we can refine it further."
    
    return {"messages": [response], "plan": state["plan"], "thought": state["thought"], "final_response": state["final_response"]}
