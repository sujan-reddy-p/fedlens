import pytest

from app.agent.graph import (
    LocalInterpreter,
    OpenRouterInterpreter,
    normalize_query_payload,
    parse_json_object,
)


def test_parse_json_object_accepts_markdown_wrapped_json() -> None:
    assert parse_json_object('```json\n{"intent": "agency_spending"}\n```') == {
        "intent": "agency_spending"
    }


@pytest.mark.asyncio
async def test_local_interpreter_extracts_fiscal_year_and_metric() -> None:
    query = await LocalInterpreter().interpret("How much did NASA spend in FY2024 outlays?")

    assert query.agency == "NASA"
    assert query.start_date.isoformat() == "2023-10-01"
    assert query.end_date.isoformat() == "2024-09-30"
    assert query.metric == "outlays"


def test_normalize_query_payload_converts_year_shorthand_to_fiscal_bounds() -> None:
    assert normalize_query_payload({"start_date": "2025", "end_date": "FY2025"}) == {
        "start_date": "2024-10-01",
        "end_date": "2025-09-30",
    }


@pytest.mark.asyncio
async def test_openrouter_interpreter_falls_back_when_free_model_returns_non_json() -> None:
    class NonJsonModel:
        async def ainvoke(self, messages):
            return type("Response", (), {"content": "I cannot format JSON."})()

    query = await OpenRouterInterpreter(NonJsonModel()).interpret("How much did NASA spend in FY2025?")

    assert query.agency == "NASA"
    assert query.start_date.isoformat() == "2024-10-01"
