import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.database.models import Agency, SpendingRecord
from app.database.session import session_scope

DEMO_SOURCE = "https://demo.fedlens.local/sample-data"


async def seed_demo_data() -> None:
    async with session_scope() as session:
        existing = await session.scalar(select(SpendingRecord.id).limit(1))
        if existing is not None:
            print("Seed skipped: spending_records already contains data.")
            return

        agencies = [
            Agency(code="NASA", name="National Aeronautics and Space Administration", aliases="NASA"),
            Agency(code="DOD", name="Department of Defense", aliases="DOD, Defense"),
            Agency(code="DOE", name="Department of Energy", aliases="DOE, Energy"),
        ]
        session.add_all(agencies)

        rows: list[SpendingRecord] = []
        values = {
            "NASA": {2023: (28_400_000_000, 26_900_000_000), 2024: (30_100_000_000, 28_700_000_000), 2025: (31_600_000_000, 30_200_000_000)},
            "DOD": {2023: (816_700_000_000, 785_000_000_000), 2024: (841_400_000_000, 809_500_000_000), 2025: (886_000_000_000, 851_000_000_000)},
            "DOE": {2023: (48_200_000_000, 45_600_000_000), 2024: (51_600_000_000, 48_900_000_000), 2025: (53_900_000_000, 51_200_000_000)},
        }
        for agency_code, yearly_values in values.items():
            for fiscal_year, (obligations, outlays) in yearly_values.items():
                rows.append(
                    SpendingRecord(
                        agency_code=agency_code,
                        fiscal_year=fiscal_year,
                        period_start=date(fiscal_year - 1, 10, 1),
                        period_end=date(fiscal_year, 9, 30),
                        category="All spending",
                        obligations=Decimal(obligations),
                        outlays=Decimal(outlays),
                        source_url=DEMO_SOURCE,
                        is_demo=True,
                    )
                )
        session.add_all(rows)
        await session.commit()
    print(f"Inserted {len(rows)} clearly labeled demo spending records.")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
