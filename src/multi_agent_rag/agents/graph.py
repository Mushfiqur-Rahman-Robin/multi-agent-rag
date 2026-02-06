from langgraph.graph import END, StateGraph

from src.multi_agent_rag.agents.coding import coding_agent
from src.multi_agent_rag.agents.planning import planning_agent
from src.multi_agent_rag.agents.research import research_agent
from src.multi_agent_rag.agents.router import direct_responder, router_node
from src.multi_agent_rag.core.state import AgentState


def create_multi_agent_graph():
    """
    Constructs and compiles the StateGraph for the multi-agent RAG system.

    The graph follows a star pattern where a 'router' node determines the flow
    between specialized agents (researcher, planner, coder) and eventually
    routes to a 'responder' for the final output.

    Returns:
        CompiledStateGraph: The ready-to-use computational graph.
    """
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("researcher", research_agent)
    workflow.add_node("planner", planning_agent)
    workflow.add_node("coder", coding_agent)
    workflow.add_node("responder", direct_responder)

    # Define Edges with Routing Logic
    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        lambda x: x["next_step"],
        {
            "research": "researcher",
            "plan": "planner",
            "code": "coder",
            "respond": "responder",
        },
    )

    # After each agent completes, go back to router to decide if more work is needed
    workflow.add_edge("researcher", "router")
    workflow.add_edge("planner", "router")
    workflow.add_edge("coder", "router")
    # responder is the exit point for the user
    workflow.add_edge("responder", END)

    return workflow.compile()


if __name__ == "__main__":
    # Test flow
    graph = create_multi_agent_graph()
    # input_state = {"messages": [HumanMessage(content="Explain quantum computing")], "files": []}
    # result = graph.invoke(input_state)
    # print(result["code"])
    pass
