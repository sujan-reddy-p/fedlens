from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

from app.database.repositories import SpendingRepository
from app.schemas.agent_query import FedLensQuery


class SpendingDataSource(Protocol):
    async def find_agency_code(self, name: str) -> str | None: ...

    async def spending_rows(
        self,
        agency_code: str,
        start_date: date | None,
        end_date: date | None,
        metric: str,
    ) -> list[dict[str, Any]]: ...


def summarize_rows(rows: list[dict[str, Any]], group_by: str) -> dict[str, Any]:
    grouped: defaultdict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        if group_by == "month":
            label = row["period_start"].strftime("%Y-%m")
        elif group_by == "category":
            label = row["category"] or "Uncategorized"
        else:
            label = str(row["fiscal_year"])
        grouped[label] += Decimal(row["value"])

    series = [{"label": label, "value": float(value)} for label, value in sorted(grouped.items())]
    total = sum((item["value"] for item in series), 0.0)
    return {
        "status": "ok",
        "total": total,
        "series": series,
        "row_count": len(rows),
        "source_urls": sorted({row["source_url"] for row in rows}),
        "summary": f"The selected records total ${total:,.2f} across {len(rows)} database records.",
    }


class AgencySpendingTool:
    def __init__(self, data_source: SpendingDataSource) -> None:
        self.data_source = data_source

    async def run(self, query: FedLensQuery) -> dict[str, Any]:
        if query.intent == "agency_comparison":
            return await self._run_comparison(query)
        if not query.agency:
            return {"status": "invalid", "summary": "An agency is required."}
        rows = await self._rows_for_agency(query.agency, query)
        if rows is None:
            return {"status": "not_found", "summary": f"No agency matched '{query.agency}'."}
        return summarize_rows(rows, query.group_by)

    async def _rows_for_agency(
        self,
        agency_name: str,
        query: FedLensQuery,
    ) -> list[dict[str, Any]] | None:
        code = await self.data_source.find_agency_code(agency_name)
        if not code:
            return None
        return await self.data_source.spending_rows(
            code,
            query.start_date,
            query.end_date,
            query.metric,
        )

    async def _run_comparison(self, query: FedLensQuery) -> dict[str, Any]:
        if len(query.agencies) < 2:
            return {"status": "invalid", "summary": "At least two agencies are required for comparison."}

        comparison_series: list[dict[str, Any]] = []
        totals: list[dict[str, Any]] = []
        source_urls: set[str] = set()
        row_count = 0
        for agency_name in query.agencies:
            rows = await self._rows_for_agency(agency_name, query)
            if rows is None:
                return {"status": "not_found", "summary": f"No agency matched '{agency_name}'."}
            summary = summarize_rows(rows, query.group_by)
            totals.append({"label": agency_name, "value": summary["total"], "unit": "USD"})
            comparison_series.extend(
                {
                    "label": item["label"],
                    "agency": agency_name,
                    "value": item["value"],
                }
                for item in summary["series"]
            )
            source_urls.update(summary["source_urls"])
            row_count += summary["row_count"]

        total = sum((item["value"] for item in totals), 0.0)
        totals_text = "; ".join(f"{item['label']}: ${item['value']:,.2f}" for item in totals)
        return {
            "status": "ok",
            "total": total,
            "totals_by_agency": totals,
            "series": comparison_series,
            "visualization_type": "bar",
            "row_count": row_count,
            "source_urls": sorted(source_urls),
            "summary": f"Comparison totals: {totals_text} across {row_count} database records.",
        }


class PostgresAgencySpendingTool(AgencySpendingTool):
    """Adapter kept separate so graph nodes do not know SQLAlchemy details."""

    def __init__(self, repository: SpendingRepository) -> None:
        super().__init__(repository)
