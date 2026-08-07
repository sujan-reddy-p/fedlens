from decimal import Decimal

import pytest

from app.ingestion.usaspending import (
    AgencyReference,
    USAspendingIngestionError,
    USAspendingIngestor,
)


class FakeUSAspendingClient:
    def __init__(self, payloads: dict[str, dict]) -> None:
        self.payloads = payloads

    async def get(self, path: str, params: dict | None = None) -> dict:
        key = path if not params else f"{path}?fiscal_year={params['fiscal_year']}"
        return self.payloads[key]

    def url_for(self, path: str, params: dict | None = None) -> str:
        query = "" if not params else f"?fiscal_year={params['fiscal_year']}"
        return f"https://api.usaspending.gov{path}{query}"


@pytest.mark.asyncio
async def test_resolves_agency_and_normalizes_annual_metrics() -> None:
    client = FakeUSAspendingClient(
        {
            "/api/v2/references/toptier_agencies/": {
                "results": [
                    {
                        "toptier_code": "080",
                        "agency_name": "National Aeronautics and Space Administration",
                        "abbreviation": "NASA",
                        "agency_slug": "national-aeronautics-and-space-administration",
                    }
                ]
            },
            "/api/v2/agency/080/budgetary_resources/?fiscal_year=2024": {
                "agency_data_by_year": [
                    {
                        "fiscal_year": 2024,
                        "agency_total_obligated": 27170027696.15,
                        "agency_total_outlayed": 27107223860.04,
                    },
                    {
                        "fiscal_year": 2023,
                        "agency_total_obligated": 28276054721.70,
                        "agency_total_outlayed": 27335465829.21,
                    },
                ]
            },
        }
    )
    ingestor = USAspendingIngestor(client)

    agency = await ingestor.resolve_agency("NASA")
    records = await ingestor.fetch_annual_spending(agency, 2023, 2024)

    assert agency.code == "080"
    assert [record.fiscal_year for record in records] == [2023, 2024]
    assert records[0].obligations == Decimal("28276054721.7")
    assert records[1].outlays == Decimal("27107223860.04")
    assert records[1].source_url.endswith("fiscal_year=2024")


@pytest.mark.asyncio
async def test_rejects_missing_requested_fiscal_year() -> None:
    client = FakeUSAspendingClient(
        {
            "/api/v2/agency/080/budgetary_resources/?fiscal_year=2024": {
                "agency_data_by_year": [
                    {
                        "fiscal_year": 2024,
                        "agency_total_obligated": 10,
                        "agency_total_outlayed": 9,
                    }
                ]
            }
        }
    )
    ingestor = USAspendingIngestor(client)
    agency = AgencyReference("080", "NASA", "NASA", "nasa")

    with pytest.raises(USAspendingIngestionError, match="FY2023"):
        await ingestor.fetch_annual_spending(agency, 2023, 2024)
