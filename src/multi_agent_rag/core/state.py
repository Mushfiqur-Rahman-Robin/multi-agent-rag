import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """
    The shared state object passed through the multi-agent graph.

    Using total=False allows optional fields with sensible defaults.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    research_output: str
    plan: str
    code: str
    thought: str
    final_response: str
    next_step: str
    files: list[str]  # Paths to uploaded files
    model: str | None  # User-selected model
    loop_count: int | None  # Tracks routing cycles to prevent infinite loops
