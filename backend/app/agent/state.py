from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    message: str
    query: dict[str, Any] | None
    tool_result: dict[str, Any] | None
    answer: str
    key_numbers: list[dict[str, Any]]
    visualizations: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    activity: list[dict[str, str]]
    warnings: list[str]
    clarification: str | None


def initial_state(message: str) -> AgentState:
    return {
        "message": message,
        "query": None,
        "tool_result": None,
        "answer": "",
        "key_numbers": [],
        "visualizations": [],
        "sources": [],
        "activity": [],
        "warnings": [],
        "clarification": None,
    }
