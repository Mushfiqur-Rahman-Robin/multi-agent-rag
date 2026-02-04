from langchain_google_genai import ChatGoogleGenerativeAI
from src.multi_agent_rag.core.config import PLANNER_MODEL, GEMINI_API_KEY
from src.multi_agent_rag.core.logging_config import logger
from langchain_core.messages import SystemMessage

def planning_agent(state):
    llm = ChatGoogleGenerativeAI(model=PLANNER_MODEL, google_api_key=GEMINI_API_KEY)
    
    research_context = state.get("research_output", "No research data available.")
    
    messages = [
        SystemMessage(content=f"You are a strategic planning agent. Based on the following research data, create a detailed step-by-step plan/draft for the final output. The plan should be structured and serve as a roadmap for the coding agent.\n\nResearch Data:\n{research_context}")
    ] + state["messages"]
    
    response = llm.invoke(messages)
    state["plan"] = response.content
    
    return {"messages": [response], "plan": state["plan"]}
