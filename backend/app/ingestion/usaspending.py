from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.clients.usaspending_client import USAspendingClient


class USAspendingIngestionError(RuntimeError):
    """Raised when the upstream response cannot be safely normalized."""


@dataclass(frozen=True)
class AgencyReference:
    code: str
    name: str
    abbreviation: str
    slug: str


@dataclass(frozen=True)
class AnnualSpending:
    agency_code: str
    fiscal_year: int
    obligations: Decimal
    outlays: Decimal
    source_url: str


def _normalized(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _decimal(value: Any, field_name: str) -> Decimal:
    if value is None:
        return Decimal(0)
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise USAspendingIngestionError(f"Invalid {field_name} value: {value!r}") from exc


class USAspendingIngestor:
    def __init__(self, client: USAspendingClient | None = None) -> None:
        self.client = client or USAspendingClient()

    async def list_agencies(self) -> list[AgencyReference]:
        payload = await self.client.get("/api/v2/references/toptier_agencies/")
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise USAspendingIngestionError("USAspending agency response has no results list")

        agencies: list[AgencyReference] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            code = item.get("toptier_code")
            name = item.get("agency_name")
            abbreviation = item.get("abbreviation") or ""
            slug = item.get("agency_slug") or ""
            if code and name:
                agencies.append(AgencyReference(str(code), str(name), str(abbreviation), str(slug)))
        return agencies

    @staticmethod
    def _resolve_from_references(
        requested_name: str,
        references: list[AgencyReference],
    ) -> AgencyReference:
        requested = _normalized(requested_name)
        for agency in references:
            candidates = {_normalized(agency.name), _normalized(agency.abbreviation), _normalized(agency.slug)}
            if requested in candidates:
                return agency
        raise USAspendingIngestionError(f"No USAspending top-tier agency matched {requested_name!r}")

    async def resolve_agency(self, requested_name: str) -> AgencyReference:
        return (await self.resolve_agencies([requested_name]))[0]

    async def resolve_agencies(self, requested_names: list[str]) -> list[AgencyReference]:
        references = await self.list_agencies()
        return [self._resolve_from_references(name, references) for name in requested_names]

    async def fetch_annual_spending(
        self,
        agency: AgencyReference,
        start_year: int,
        end_year: int,
    ) -> list[AnnualSpending]:
        if start_year > end_year:
            raise ValueError("start_year must be less than or equal to end_year")

        path = f"/api/v2/agency/{agency.code}/budgetary_resources/"
        payload = await self.client.get(path, {"fiscal_year": end_year})
        annual_rows = payload.get("agency_data_by_year")
        if not isinstance(annual_rows, list):
            raise USAspendingIngestionError("USAspending budget response has no annual data list")

        source_url = self.client.url_for(path, {"fiscal_year": end_year})
        records: list[AnnualSpending] = []
        for item in annual_rows:
            if not isinstance(item, dict):
                continue
            fiscal_year = item.get("fiscal_year")
            if not isinstance(fiscal_year, int) or not start_year <= fiscal_year <= end_year:
                continue
            required_fields = ("agency_total_obligated", "agency_total_outlayed")
            if any(field not in item for field in required_fields):
                raise USAspendingIngestionError(
                    f"USAspending budget row for FY{fiscal_year} is missing a required metric"
                )
            records.append(
                AnnualSpending(
                    agency_code=agency.code,
                    fiscal_year=fiscal_year,
                    obligations=_decimal(item["agency_total_obligated"], "agency_total_obligated"),
                    outlays=_decimal(item["agency_total_outlayed"], "agency_total_outlayed"),
                    source_url=source_url,
                )
            )

        loaded_years = {record.fiscal_year for record in records}
        missing_years = set(range(start_year, end_year + 1)) - loaded_years
        if missing_years:
            missing = ", ".join(str(year) for year in sorted(missing_years))
            raise USAspendingIngestionError(
                f"USAspending returned no annual data for {agency.name}: FY{missing}"
            )
        return sorted(records, key=lambda record: record.fiscal_year)


def fiscal_year_dates(fiscal_year: int) -> tuple[date, date]:
    return date(fiscal_year - 1, 10, 1), date(fiscal_year, 9, 30)
