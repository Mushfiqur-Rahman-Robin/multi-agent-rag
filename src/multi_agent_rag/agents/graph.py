from langgraph.graph import StateGraph, END
from src.multi_agent_rag.core.state import AgentState
from src.multi_agent_rag.core.config import SEARCH_MODEL, PLANNER_MODEL, CODER_MODEL, GEMINI_API_KEY
from src.multi_agent_rag.agents.research import research_agent
from src.multi_agent_rag.agents.planning import planning_agent
from src.multi_agent_rag.agents.coding import coding_agent

def create_multi_agent_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("researcher", research_agent)
    workflow.add_node("planner", planning_agent)
    workflow.add_node("coder", coding_agent)

    # Define Edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", END)

    return workflow.compile()

if __name__ == "__main__":
    # Test flow
    graph = create_multi_agent_graph()
    # input_state = {"messages": [HumanMessage(content="Explain quantum computing")], "files": []}
    # result = graph.invoke(input_state)
    # print(result["code"])
    pass
