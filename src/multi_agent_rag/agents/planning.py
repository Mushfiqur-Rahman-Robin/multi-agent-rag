"""
Planning agent module for the multi-agent RAG system.

Handles the strategic planning phase: creating roadmaps, outlines, and structured approaches.
"""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src.multi_agent_rag.core.config import OPENAI_API_KEY, PLANNER_MODEL
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.core.prompts import PROMPTS
from src.multi_agent_rag.core.utils import get_text_content


async def planning_agent(state):
    """
    Handles the planning phase of the workflow.

    This agent takes the synthesized research data and the user's requirements
    to build a strategic, step-by-step roadmap or draft.

    Args:
        state (dict): The current graph state.

    Returns:
        dict: State updates containing the formal 'plan', a thought, and messages.
    """
    logger.info("Planning agent initiated.")
    selected_model = state.get("model") or PLANNER_MODEL
    llm = ChatOpenAI(
        model=selected_model, openai_api_key=OPENAI_API_KEY, temperature=0.5
    )

    # Get research context from state
    research_context = state.get("research_output", "")

    # Fallback: try to find research data in message history
    if not research_context:
        for msg in reversed(state.get("messages", [])):
            text_content = get_text_content(msg.content)
            if any(
                keyword in text_content.lower()
                for keyword in [
                    "research data",
                    "knowledge base results",
                    "found the following",
                    "here's what i found",
                ]
            ):
                research_context = text_content
                break

    research_context = (
        research_context
        or "No explicit research data available. Create a plan based on general best practices and the user's request."
    )

    # Build messages for the planning LLM
    system_content = PROMPTS["planning_system"].format(
        research_context=research_context
    )

    messages = [SystemMessage(content=system_content)] + state["messages"]

    response = await llm.ainvoke(messages)
    plan_output = response.content
    thought = "Strategic plan drafted based on available context."

    logger.info(f"Planning Agent Thought: {thought}")

    # NOTE: We do NOT set final_response here - let the router decide when to respond
    # The plan is stored, and the router will determine if more work is needed
    return {"messages": [response], "plan": plan_output, "thought": thought}
