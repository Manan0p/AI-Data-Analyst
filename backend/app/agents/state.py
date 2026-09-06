from typing import Any, Optional, TypedDict
from langgraph.graph import add_messages
from typing_extensions import Annotated


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Chat / conversation message history
    dataset_id: str
    schema: dict
    intent: Optional[str]
    tool: Optional[str]
    tool_args: Optional[dict[str, Any]]
    tool_result: Optional[dict[str, Any]]
    error: Optional[str]
    retries: int
    final_answer: Optional[dict[str, Any]]
    datasets: Optional[dict[str, Any]]  # Map of registered table names to DataFrames
