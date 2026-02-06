"""
Router module for the multi-agent RAG system.

Contains the main orchestrator that routes requests to appropriate agents
and the direct responder for generating final user-facing responses.
"""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src.multi_agent_rag.core.config import DEFAULT_MODEL, OPENAI_API_KEY
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.core.prompts import PROMPTS


def get_text_content(msg) -> str:
    """
    Safely extract text content from potentially multimodal messages.

    Args:
        msg: A LangChain message object.

    Returns:
        str: The extracted text content.
    """
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                text_parts.append(c.get("text", ""))
            elif hasattr(c, "type") and c.type == "text":
                text_parts.append(c.text)
        return " ".join(text_parts)
    return str(content)


async def router_node(state: dict) -> dict:
    """
    The main orchestrator node that decides the next step based on conversation context.

    It analyzes the current state (research, plan, code, final_response) and the
    conversation history to route the request appropriately.

    Args:
        state (dict): The current state of the LangGraph.

    Returns:
        dict: The updated state with 'next_step' and 'thought'.
    """
    # Initialize or increment loop count
    current_loop = state.get("loop_count") or 0
    current_loop += 1

    logger.info(f"Router node evaluating (Cycle {current_loop}).")

    # Safety break for infinite loops - more aggressive
    if current_loop > 3:
        logger.warning(f"Max loop count ({current_loop}) reached. Forcing response.")
        return {
            "next_step": "respond",
            "thought": "Completing request - maximum workflow cycles reached.",
            "loop_count": current_loop,
        }

    selected_model = state.get("model") or DEFAULT_MODEL
    llm = ChatOpenAI(model=selected_model, openai_api_key=OPENAI_API_KEY, temperature=0)

    messages = state.get("messages", [])
    last_message = get_text_content(messages[-1]) if messages else ""

    # Build concise history for context (limit to recent messages)
    history_elements = []
    for m in messages[-6:-1]:  # Last 5 messages before current, for context
        content = get_text_content(m)
        role = getattr(m, "type", "unknown")
        # Truncate long messages
        truncated = content[:200] + "..." if len(content) > 200 else content
        history_elements.append(f"{role}: {truncated}")
    history_str = (
        "\n".join(history_elements) if history_elements else "No prior messages."
    )

    # State markers for the prompt
    has_research = bool(state.get("research_output"))
    has_plan = bool(state.get("plan"))
    has_code = bool(state.get("code"))
    has_final_response = bool(state.get("final_response"))

    prompt = PROMPTS["router"].format(
        has_research=has_research,
        has_plan=has_plan,
        has_code=has_code,
        has_final_response=has_final_response,
        history_str=history_str,
        last_message=last_message,
    )

    response = await llm.ainvoke([SystemMessage(content=prompt)])
    decision_raw = response.content.strip().lower()

    # Parse decision more robustly
    if "research" in decision_raw:
        decision = "research"
        thought = "Initiating research phase to gather information."
    elif "plan" in decision_raw:
        decision = "plan"
        thought = "Creating strategic plan based on available data."
    elif "code" in decision_raw:
        # Anti-loop check: if code already exists and we're being asked to code again
        if has_code and current_loop > 1:
            logger.info("Code already exists and loop detected. Switching to respond.")
            decision = "respond"
            thought = "Code is ready. Presenting the implementation."
        else:
            decision = "code"
            thought = "Moving to implementation/coding phase."
    else:
        decision = "respond"
        thought = "Generating direct response."

    logger.info(
        f"Orchestrator decision: {decision} (Cycle: {current_loop}, Reason: {thought})"
    )

    return {"next_step": decision, "thought": thought, "loop_count": current_loop}


async def direct_responder(state: dict) -> dict:
    """
    Generates a final response to the user, synthesizing all available context.

    This is the exit point of the workflow. It consumes research data, plans,
    and code (if available) to provide a comprehensive, user-friendly response.

    Args:
        state (dict): The current state of the LangGraph.

    Returns:
        dict: State updates containing the final AI message and metadata.
    """
    logger.info("Direct responder activated.")
    selected_model = state.get("model") or DEFAULT_MODEL
    llm = ChatOpenAI(
        model=selected_model, openai_api_key=OPENAI_API_KEY, temperature=0.7
    )

    # Build comprehensive context from available state
    context_parts = []

    research_context = state.get("research_output", "")
    if research_context:
        context_parts.append(f"RESEARCH DATA:\n{research_context}")

    plan_context = state.get("plan", "")
    if plan_context:
        context_parts.append(f"STRATEGIC PLAN:\n{plan_context}")

    code_context = state.get("code", "")
    if code_context:
        context_parts.append(f"IMPLEMENTATION CODE:\n{code_context}")

    # Build the system prompt with context
    system_prompt = PROMPTS["direct_response_system"]

    if context_parts:
        combined_context = "\n\n---\n\n".join(context_parts)
        system_prompt += (
            f"\n\nAVAILABLE CONTEXT FROM THIS SESSION:\n{combined_context}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. PROVIDE A COMPREHENSIVE ANSWER using all the context provided above.\n"
            "2. **MANDATORY**: IF 'IMPLEMENTATION CODE' IS PRESENT IN THE CONTEXT ABOVE, YOU MUST INCLUDE THE ENTIRE CODE BLOCK IN YOUR FINAL RESPONSE. DO NOT SUMMARIZE OR OMIT THE CODE.\n"
            "3. Reference findings from research or strategic plans where relevant to add value.\n"
            "4. Use clear Markdown formatting with proper headings and code syntax highlighting."
        )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = await llm.ainvoke(messages)
    final_response = response.content

    # Determine the thought based on what context was used
    if code_context:
        thought = "Presenting implementation with explanation."
    elif plan_context:
        thought = "Delivering strategic plan to user."
    elif research_context:
        thought = "Synthesizing answer from gathered research."
    else:
        thought = "Generated a direct response."

    logger.info(f"Direct responder thought: {thought}")

    return {
        "messages": [response],
        "final_response": final_response,
        "thought": thought,
    }
