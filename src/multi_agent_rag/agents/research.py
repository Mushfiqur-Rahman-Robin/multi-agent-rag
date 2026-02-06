"""
Research agent module for the multi-agent RAG system.

Handles the research phase: knowledge base queries, web searches, and information synthesis.
Includes caching for repeated queries to improve performance and reduce API costs.
"""

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.multi_agent_rag.core.config import OPENAI_API_KEY, SEARCH_MODEL
from src.multi_agent_rag.core.logging_config import logger
from src.multi_agent_rag.core.prompts import PROMPTS
from src.multi_agent_rag.core.tools import google_search, vector_search
from src.multi_agent_rag.core.utils import get_text_content

# Import cache service (graceful if Redis unavailable)
try:
    from src.multi_agent_rag.services.cache_service import cache_service
except ImportError:
    cache_service = None


def research_agent(state: dict) -> dict:
    """
    Handles the research phase of the workflow.

    This agent follows a strict protocol:
    1. Check cache for previous research on similar queries
    2. Mandatory check of the internal Knowledge Base via 'vector_search'
    3. Fallback to 'google_search' if internal info is insufficient or missing
    4. Final synthesis of all findings into a structured report
    5. Cache the results for future queries

    Args:
        state (dict): The current graph state.

    Returns:
        dict: State updates containing research summary and thought.
    """
    logger.info("Research agent initiated.")

    # Extract the user's query for cache key generation
    messages = state.get("messages", [])
    if not messages:
        return {
            "research_output": "No messages to research.",
            "thought": "No input provided for research.",
        }

    # Get the last human message as the research query
    user_query = ""
    for msg in reversed(messages):
        msg_type = getattr(msg, "type", None)
        if msg_type == "human":
            user_query = get_text_content(msg)
            break

    # Check cache first (if available)
    if cache_service and cache_service.is_available and user_query:
        cached_research = cache_service.get_research_cache(user_query)
        if cached_research:
            logger.info(f"Research cache HIT for query: {user_query[:50]}...")
            return {
                "messages": [SystemMessage(content=cached_research)],
                "research_output": cached_research,
                "thought": "Retrieved research from cache.",
            }
        logger.debug(f"Research cache MISS for query: {user_query[:50]}...")

    # No cache hit - perform research
    selected_model = state.get("model") or SEARCH_MODEL
    llm = ChatOpenAI(model=selected_model, openai_api_key=OPENAI_API_KEY, temperature=0)
    llm_with_tools = llm.bind_tools([google_search, vector_search])

    # Build local message context for this research session
    current_messages = [SystemMessage(content=PROMPTS["research_system"]), *messages]

    # Max iterations to avoid infinite tool loops
    max_iterations = 3
    research_summary = ""
    thought = "Gathering information..."

    import time

    start_time = time.time()
    for i in range(max_iterations):
        try:
            iter_start = time.time()
            response = llm_with_tools.invoke(current_messages)
            logger.info(f"LLM tool-call decision took {time.time() - iter_start:.2f}s")
            current_messages.append(response)

            if not response.tool_calls:
                # LLM is done with tools, this is the summary
                research_summary = response.content
                break

            thought = f"Researching (Step {i + 1}/{max_iterations})..."

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                try:
                    tool_start = time.time()
                    if tool_name == "google_search":
                        logger.info(f"Executing google_search: {tool_args}")
                        result = google_search.invoke(tool_args)
                    elif tool_name == "vector_search":
                        logger.info(f"Executing vector_search: {tool_args}")
                        result = vector_search.invoke(tool_args)
                    else:
                        result = f"Unknown tool: {tool_name}"

                    logger.info(
                        f"Tool {tool_name} took {time.time() - tool_start:.2f}s"
                    )

                    current_messages.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                    )
                except Exception as tool_error:
                    logger.error(f"Tool {tool_name} failed: {tool_error}")
                    current_messages.append(
                        ToolMessage(
                            content=f"Tool error: {tool_error!s}",
                            tool_call_id=tool_call["id"],
                        )
                    )

        except Exception as e:
            logger.error(f"Research iteration {i + 1} failed: {e}")
            break

    # Final synthesis if we didn't get a clean summary
    if not research_summary or not research_summary.strip():
        synthesis_prompt = """Based on the information gathered above, provide a comprehensive,
        structured research summary that directly answers the user's query.
        Be thorough but concise. Do not use any tools."""

        try:
            synth_start = time.time()
            final_synth = llm.invoke(
                [*current_messages, SystemMessage(content=synthesis_prompt)]
            )
            logger.info(
                f"Research final synthesis took {time.time() - synth_start:.2f}s"
            )
            research_summary = final_synth.content
            current_messages.append(final_synth)
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            research_summary = "Unable to synthesize research findings."

    total_research_time = time.time() - start_time
    logger.info(f"Total research workflow took {total_research_time:.2f}s")

    # Cache the research results
    if cache_service and cache_service.is_available and user_query and research_summary:
        cache_service.set_research_cache(user_query, research_summary)
        logger.debug(f"Research cached for query: {user_query[:50]}...")

    thought = "Research complete. Information gathered and synthesized."
    logger.info(
        f"Research Agent completed. Summary length: {len(research_summary)} chars"
    )

    return {
        "messages": [current_messages[-1]],
        "research_output": research_summary,
        "thought": thought,
    }
