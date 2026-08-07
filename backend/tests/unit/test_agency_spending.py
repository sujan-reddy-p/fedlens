from datetime import date

import pytest

from app.schemas.agent_query import FedLensQuery
from app.tools.agency_spending import AgencySpendingTool


class FakeSpendingSource:
    async def find_agency_code(self, name: str) -> str | None:
        return name if name in {"NASA", "DOD"} else None

    async def spending_rows(
        self,
        agency_code: str,
        start_date: date | None,
        end_date: date | None,
        metric: str,
    ) -> list[dict]:
        multiplier = 1 if agency_code == "NASA" else 2
        return [
            {"period_start": date(2024, 1, 1), "fiscal_year": 2024, "category": "Research", "value": 100 * multiplier, "source_url": "https://example.gov/a"},
            {"period_start": date(2025, 1, 1), "fiscal_year": 2025, "category": "Research", "value": 125 * multiplier, "source_url": "https://example.gov/a"},
        ]


@pytest.mark.asyncio
async def test_agency_spending_tool_aggregates_by_year() -> None:
    result = await AgencySpendingTool(FakeSpendingSource()).run(
        FedLensQuery(intent="agency_spending", agency="NASA")
    )

    assert result["status"] == "ok"
    assert result["total"] == 225
    assert result["series"] == [
        {"label": "2024", "value": 100.0},
        {"label": "2025", "value": 125.0},
    ]


@pytest.mark.asyncio
async def test_agency_comparison_returns_per_agency_totals_and_series() -> None:
    result = await AgencySpendingTool(FakeSpendingSource()).run(
        FedLensQuery(intent="agency_comparison", agencies=["NASA", "DOD"])
    )

    assert result["status"] == "ok"
    assert result["totals_by_agency"] == [
        {"label": "NASA", "value": 225.0, "unit": "USD"},
        {"label": "DOD", "value": 450.0, "unit": "USD"},
    ]
    assert result["visualization_type"] == "bar"
    assert result["row_count"] == 4
