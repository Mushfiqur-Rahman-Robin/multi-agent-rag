from typing import TypedDict, Annotated, List, Union
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    research_output: str
    plan: str
    code: str
    next_step: str
    files: List[str]  # Paths to uploaded files
