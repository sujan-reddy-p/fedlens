import argparse
import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, select, update

from app.database.models import Agency, IngestionRun, SpendingRecord
from app.database.session import session_scope
from app.ingestion.usaspending import (
    AgencyReference,
    AnnualSpending,
    USAspendingIngestor,
    fiscal_year_dates,
)

DEFAULT_AGENCIES = ("NASA", "DOD", "DOE")
SOURCE_NAME = "USAspending.gov"


async def _start_run() -> int:
    async with session_scope() as session:
        run = IngestionRun(source=SOURCE_NAME, status="running")
        session.add(run)
        await session.flush()
        run_id = run.id
        await session.commit()
        return run_id


async def _finish_run(run_id: int, status: str, records_loaded: int, error: str | None = None) -> None:
    async with session_scope() as session:
        run = await session.get(IngestionRun, run_id)
        if run is None:
            raise RuntimeError(f"Ingestion run {run_id} was not found")
        run.status = status
        run.records_loaded = records_loaded
        run.error_message = error
        run.completed_at = datetime.now(UTC)
        await session.commit()


async def _upsert_records(
    run_id: int,
    agencies: list[tuple[AgencyReference, list[AnnualSpending]]],
    replace_demo: bool,
) -> int:
    records_loaded = 0
    async with session_scope() as session:
        for agency_reference, records in agencies:
            aliases = ", ".join(
                value
                for value in (agency_reference.abbreviation, agency_reference.slug)
                if value
            )
            agency = await session.get(Agency, agency_reference.code)
            if agency is None:
                agency = await session.scalar(
                    select(Agency).where(Agency.name == agency_reference.name)
                )
            if agency is not None and agency.code != agency_reference.code:
                legacy_code = agency.code
                agency.name = f"{agency.name} (legacy)"
                await session.flush()
                replacement = Agency(
                    code=agency_reference.code,
                    name=agency_reference.name,
                    aliases=aliases,
                )
                session.add(replacement)
                await session.flush()
                await session.execute(
                    update(SpendingRecord)
                    .where(SpendingRecord.agency_code == legacy_code)
                    .values(agency_code=agency_reference.code)
                )
                await session.delete(agency)
                await session.flush()
                agency = replacement
            if agency is None:
                agency = Agency(
                    code=agency_reference.code,
                    name=agency_reference.name,
                    aliases=aliases,
                )
                session.add(agency)
                await session.flush()
            else:
                agency.name = agency_reference.name
                agency.aliases = aliases

            if replace_demo:
                await session.execute(
                    delete(SpendingRecord).where(
                        SpendingRecord.agency_code == agency_reference.code,
                        SpendingRecord.is_demo.is_(True),
                    )
                )

            for record in records:
                period_start, period_end = fiscal_year_dates(record.fiscal_year)
                existing = await session.scalar(
                    select(SpendingRecord).where(
                        SpendingRecord.agency_code == record.agency_code,
                        SpendingRecord.fiscal_year == record.fiscal_year,
                        SpendingRecord.category == "All spending",
                    )
                )
                if existing is None:
                    existing = SpendingRecord(
                        agency_code=record.agency_code,
                        fiscal_year=record.fiscal_year,
                        period_start=period_start,
                        period_end=period_end,
                        category="All spending",
                    )
                    session.add(existing)
                existing.period_start = period_start
                existing.period_end = period_end
                existing.obligations = record.obligations
                existing.outlays = record.outlays
                existing.source_url = record.source_url
                existing.is_demo = False
                records_loaded += 1

        run = await session.get(IngestionRun, run_id)
        if run is None:
            raise RuntimeError(f"Ingestion run {run_id} was not found")
        run.status = "succeeded"
        run.records_loaded = records_loaded
        run.completed_at = datetime.now(UTC)
        await session.commit()
    return records_loaded


async def ingest(
    requested_agencies: list[str],
    start_year: int,
    end_year: int,
    replace_demo: bool,
) -> int:
    run_id = await _start_run()
    try:
        ingestor = USAspendingIngestor()
        resolved = []
        references = await ingestor.resolve_agencies(requested_agencies)
        for reference in references:
            records = await ingestor.fetch_annual_spending(reference, start_year, end_year)
            resolved.append((reference, records))
            print(f"Fetched {reference.name} ({reference.code}): {len(records)} annual records")
        return await _upsert_records(run_id, resolved, replace_demo)
    except Exception as exc:
        await _finish_run(run_id, "failed", 0, str(exc))
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load official annual agency spending from USAspending.gov")
    parser.add_argument("--agencies", nargs="+", default=list(DEFAULT_AGENCIES))
    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--replace-demo",
        action="store_true",
        help="Remove demo rows for the selected agencies before loading official rows",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    loaded = asyncio.run(ingest(args.agencies, args.start_year, args.end_year, args.replace_demo))
    print(f"Loaded {loaded} official USAspending records into Neon.")
