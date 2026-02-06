"""
Coding agent module for the multi-agent RAG system.

Handles the implementation phase: code generation, execution, and verification.
"""

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.multi_agent_rag.core.config import CODER_MODEL, OPENAI_API_KEY
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.core.prompts import PROMPTS
from src.multi_agent_rag.core.tools import python_repl
from src.multi_agent_rag.core.utils import get_text_content


def coding_agent(state):
    """
    Handles the implementation phase of the workflow.

    This agent takes the agreed plan and research context to produce
    actual code or documents. It can utilize the 'python_repl' tool
    to verify logic or generate dynamic outputs.

    Args:
        state (dict): The current graph state.

    Returns:
        dict: State updates containing the final 'code', a thought, and messages.
    """
    logger.info("Coding agent initiated.")
    selected_model = state.get("model") or CODER_MODEL
    llm = ChatOpenAI(model=selected_model, openai_api_key=OPENAI_API_KEY, temperature=0)
    llm_with_tools = llm.bind_tools([python_repl])

    # Gather context from state
    plan_context = state.get("plan", "")
    research_context = state.get("research_output", "")

    # Fallback: try to find context in message history if not in state
    if not plan_context:
        for msg in reversed(state.get("messages", [])):
            content_text = get_text_content(msg.content)
            if any(
                keyword in content_text.lower()
                for keyword in [
                    "step-by-step plan",
                    "drafted a plan",
                    "roadmap",
                    "phase 1",
                ]
            ):
                plan_context = content_text
                break

    if not research_context:
        for msg in reversed(state.get("messages", [])):
            content_text = get_text_content(msg.content)
            if any(
                keyword in content_text.lower()
                for keyword in [
                    "research data",
                    "knowledge base results",
                    "found the following",
                ]
            ):
                research_context = content_text
                break

    # Use placeholder text if still empty
    plan_context = (
        plan_context
        or "No explicit plan provided. Infer requirements from the user's request."
    )
    research_context = (
        research_context or "No explicit research data. Use general knowledge."
    )

    # Build messages for the coding LLM
    system_content = PROMPTS["coding_system"].format(
        plan_context=plan_context, research_context=research_context
    )

    messages = [SystemMessage(content=system_content)] + state["messages"]

    response = llm_with_tools.invoke(messages)
    new_messages = [response]

    code_output = ""
    thought = ""

    # Handle tool calls for python_repl if any
    if response.tool_calls:
        thought = (
            f"Executing code implementation ({len(response.tool_calls)} tool calls)."
        )
        for tool_call in response.tool_calls:
            if tool_call["name"] == "python_repl":
                try:
                    execution_result = python_repl.invoke(tool_call["args"])
                    new_messages.append(
                        ToolMessage(
                            content=str(execution_result), tool_call_id=tool_call["id"]
                        )
                    )
                    # The code is the input to the tool
                    code_output = tool_call["args"].get("code", str(execution_result))
                except Exception as e:
                    error_msg = f"Execution error: {e!s}"
                    new_messages.append(
                        ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                    )
                    code_output = error_msg
    else:
        # The response content IS the code
        code_output = response.content
        thought = "Generated implementation directly."

    logger.info(f"Coding Agent Thought: {thought}")

    # NOTE: We do NOT set final_response here - let the router decide when to respond
    # This prevents the router from thinking the job is done prematurely
    return {"messages": new_messages, "code": code_output, "thought": thought}
