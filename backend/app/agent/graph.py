import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Any, Protocol

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.agent.state import AgentState, initial_state
from app.config import get_settings
from app.database.repositories import SpendingRepository
from app.database.session import session_scope
from app.schemas.agent_query import FedLensQuery
from app.tools.agency_spending import PostgresAgencySpendingTool


class Interpreter(Protocol):
    async def interpret(self, message: str) -> FedLensQuery: ...


class Answerer(Protocol):
    async def answer(self, message: str, query: FedLensQuery, result: dict[str, Any]) -> str: ...


class DataTool(Protocol):
    async def run(self, query: FedLensQuery) -> dict[str, Any]: ...


class LocalInterpreter:
    """Small offline interpreter used until an LLM key is configured."""

    async def interpret(self, message: str) -> FedLensQuery:
        lowered = message.lower()
        agency_aliases = {
            "nasa": "NASA",
            "dod": "DOD",
            "department of defense": "DOD",
            "doe": "DOE",
            "department of energy": "DOE",
        }
        agencies = list(dict.fromkeys(
            canonical
            for alias, canonical in agency_aliases.items()
            if re.search(rf"\b{re.escape(alias)}\b", lowered)
        ))
        agency = agencies[0] if agencies else None
        if "compare" in lowered or "versus" in lowered:
            intent = "agency_comparison"
        elif "trend" in lowered or "over time" in lowered:
            intent = "agency_trend"
        else:
            intent = "agency_spending"
        fiscal_years = [int(year) for year in re.findall(r"\bfy\s?(20\d{2})\b", lowered)]
        start_date = end_date = None
        if fiscal_years:
            start_date = date(fiscal_years[0] - 1, 10, 1)
            end_date = date(fiscal_years[-1], 9, 30)
        group_by = "month" if "month" in lowered or "monthly" in lowered else "year"
        if "category" in lowered or "account" in lowered:
            group_by = "category"
        metric = "outlays" if "outlay" in lowered else "obligations"
        return FedLensQuery(
            intent=intent,
            agency=agency,
            agencies=agencies,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            group_by=group_by,
        )


class LocalAnswerer:
    async def answer(self, message: str, query: FedLensQuery, result: dict[str, Any]) -> str:
        if result.get("status") == "not_connected":
            return (
                "I understood this as a federal spending question, but the PostgreSQL "
                "data tool is not connected yet. The next step is loading verified data."
            )
        return result.get("summary", "The query completed successfully.")


def parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("The model did not return a JSON object")
    return json.loads(cleaned[start : end + 1])


def normalize_query_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Make common LLM shorthand dates conform to the typed query contract."""
    normalized = dict(payload)
    for field, fiscal_year_offset in (("start_date", -1), ("end_date", 0)):
        value = normalized.get(field)
        if not isinstance(value, str):
            continue
        match = re.fullmatch(r"(?:fy\s?)?(20\d{2})", value.strip(), re.IGNORECASE)
        if match:
            year = int(match.group(1))
            normalized[field] = (
                date(year + fiscal_year_offset, 10, 1)
                if field == "start_date"
                else date(year, 9, 30)
            ).isoformat()
    return normalized


class OpenRouterInterpreter:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def interpret(self, message: str) -> FedLensQuery:
        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": (
                        "Interpret the user's federal spending question. Resolve ordinary "
                        "ambiguity, but return only valid JSON matching this shape: "
                        '{"intent":"agency_spending|agency_comparison|agency_trend",'
                        '"agency":string|null,"agencies":[string],"start_date":string|null,'
                        '"end_date":string|null,"metric":"obligations|outlays",'
                        '"group_by":"year|month|category"}. For comparisons, include every '
                        'agency in agencies and at least two agencies. Use obligations for '
                        'ordinary "spending" or "spent" wording; use outlays only when the '
                        'user explicitly asks about outlays, paid, or disbursed amounts. Do '
                        'not use markdown.'
                    ),
                },
                {"role": "user", "content": message},
            ])
            payload = normalize_query_payload(parse_json_object(response.content))
            return FedLensQuery.model_validate(payload)
        except (AttributeError, TypeError, ValueError, ValidationError):
            return await LocalInterpreter().interpret(message)


class OpenRouterAnswerer:
    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def answer(self, message: str, query: FedLensQuery, result: dict[str, Any]) -> str:
        try:
            response = await self.llm.ainvoke([
                {
                    "role": "system",
                    "content": (
                        "Explain only the verified result. Never invent spending values. "
                        "State whether the result uses obligations or outlays when it "
                        "matters to the answer."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"question": message, "query": query.model_dump(mode="json"), "result": result}),
                },
            ])
            if isinstance(response.content, str) and response.content.strip():
                return response.content
        except (AttributeError, TypeError, ValueError):
            pass
        return await LocalAnswerer().answer(message, query, result)


@dataclass
class GraphResult:
    answer: str
    key_numbers: list[dict[str, Any]]
    visualizations: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    activity: list[dict[str, str]]
    warnings: list[str]


class FedLensGraph:
    def __init__(
        self,
        interpreter: Interpreter | None = None,
        answerer: Answerer | None = None,
        data_tool: DataTool | None = None,
    ) -> None:
        self.interpreter = interpreter or LocalInterpreter()
        self.answerer = answerer or LocalAnswerer()
        self.data_tool = data_tool
        builder = StateGraph(AgentState)
        builder.add_node("interpret_query", self.interpret_query)
        builder.add_node("validate_query", self.validate_query)
        builder.add_node("run_data_tool", self.run_data_tool)
        builder.add_node("generate_answer", self.generate_answer)
        builder.add_edge(START, "interpret_query")
        builder.add_edge("interpret_query", "validate_query")
        builder.add_conditional_edges("validate_query", self.route_after_validation, {"run": "run_data_tool", "clarify": END})
        builder.add_edge("run_data_tool", "generate_answer")
        builder.add_edge("generate_answer", END)
        self.compiled = builder.compile()

    async def invoke(self, message: str) -> GraphResult:
        state = await self.compiled.ainvoke(initial_state(message))
        return GraphResult(**{key: state.get(key, []) for key in ("answer", "key_numbers", "visualizations", "sources", "activity", "warnings")})

    async def interpret_query(self, state: AgentState) -> AgentState:
        query = await self.interpreter.interpret(state["message"])
        return {"query": query.model_dump(), "activity": state["activity"] + [{"type": "status", "message": "Interpreted the user query."}]}

    async def validate_query(self, state: AgentState) -> AgentState:
        query = FedLensQuery.model_validate(state["query"])
        if query.intent in {"agency_spending", "agency_trend"} and not query.agency:
            message = "Which federal agency should I analyze?"
            return {"clarification": message, "answer": message, "activity": state["activity"] + [{"type": "status", "message": "Clarification is required."}]}
        if query.intent == "agency_comparison" and len(query.agencies) < 2:
            message = "Which two or more federal agencies should I compare?"
            return {"clarification": message, "answer": message, "activity": state["activity"] + [{"type": "status", "message": "Clarification is required."}]}
        return {"query": query.model_dump(), "activity": state["activity"] + [{"type": "status", "message": "Validated the structured query."}]}

    def route_after_validation(self, state: AgentState) -> str:
        return "clarify" if state.get("clarification") else "run"

    async def run_data_tool(self, state: AgentState) -> AgentState:
        if self.data_tool is None:
            result = {"status": "not_connected", "summary": "No live PostgreSQL data tool is connected."}
            warnings = ["PostgreSQL is not connected yet."]
        else:
            result = await self.data_tool.run(FedLensQuery.model_validate(state["query"]))
            warnings = [] if result.get("status") == "ok" else [result.get("summary", "The data tool returned a limitation.")]
        key_numbers = []
        visualizations = []
        sources = []
        if result.get("status") == "ok":
            key_numbers = result.get("totals_by_agency") or [
                {"label": "Total", "value": result["total"], "unit": "USD"},
            ]
            key_numbers.append({"label": "Records analyzed", "value": result["row_count"], "unit": "records"})
            visualizations = [
                {
                    "type": result.get("visualization_type", "line"),
                    "title": "Agency spending comparison" if result.get("visualization_type") == "bar" else "Spending over time",
                    "x_key": "label",
                    "y_key": "value",
                    "unit": "USD",
                    "data": result["series"],
                }
            ]
            sources = [
                {
                    "name": "FedLens database",
                    "endpoint": url,
                    "retrieved_at": datetime.now(UTC),
                    "parameters": {"record_count": result["row_count"]},
                }
                for url in result.get("source_urls", [])
            ]
        return {
            "tool_result": result,
            "key_numbers": key_numbers,
            "visualizations": visualizations,
            "sources": sources,
            "activity": state["activity"] + [{"type": "tool", "message": "Queried PostgreSQL and ran the spending analysis."}],
            "warnings": warnings,
        }

    async def generate_answer(self, state: AgentState) -> AgentState:
        query = FedLensQuery.model_validate(state["query"])
        answer = await self.answerer.answer(state["message"], query, state["tool_result"])
        return {"answer": answer, "activity": state["activity"] + [{"type": "status", "message": "Generated an answer from the tool result."}]}


@lru_cache
def get_graph() -> FedLensGraph:
    settings = get_settings()
    if settings.app_env == "test":
        return FedLensGraph()
    if settings.llm_provider == "openrouter" and settings.openrouter_api_key and settings.llm_model:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            timeout=30,
            max_retries=0,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "FedLens",
            },
        )
        return FedLensGraph(OpenRouterInterpreter(llm), OpenRouterAnswerer(llm), get_data_tool())
    if settings.llm_provider == "openai" and settings.openai_api_key and settings.llm_model:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0,
            timeout=30,
            max_retries=0,
        )
        return FedLensGraph(OpenRouterInterpreter(llm), OpenRouterAnswerer(llm), get_data_tool())
    return FedLensGraph(data_tool=get_data_tool())


def get_data_tool() -> DataTool | None:
    settings = get_settings()
    if settings.app_env == "test" or not settings.database_url:
        return None
    return PostgresToolFactory()


class PostgresToolFactory:
    async def run(self, query: FedLensQuery) -> dict[str, Any]:
        async with session_scope() as session:
            repository = SpendingRepository(session)
            return await PostgresAgencySpendingTool(repository).run(query)
