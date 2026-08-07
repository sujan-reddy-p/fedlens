from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Agency, SpendingRecord


class SpendingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_agency_code(self, name: str) -> str | None:
        normalized = " ".join(name.split()).casefold()
        query = select(Agency).where(
            (Agency.name.ilike(normalized)) | Agency.aliases.ilike(f"%{normalized}%")
        )
        agency = (await self.session.scalars(query)).first()
        return agency.code if agency else None

    async def spending_rows(
        self,
        agency_code: str,
        start_date: date | None,
        end_date: date | None,
        metric: str,
    ) -> list[dict[str, Any]]:
        query = select(SpendingRecord).where(SpendingRecord.agency_code == agency_code)
        if start_date:
            query = query.where(SpendingRecord.period_end >= start_date)
        if end_date:
            query = query.where(SpendingRecord.period_start <= end_date)
        rows = (await self.session.scalars(query.order_by(SpendingRecord.period_start))).all()
        value_key = "obligations" if metric == "obligations" else "outlays"
        return [
            {
                "period_start": row.period_start,
                "period_end": row.period_end,
                "fiscal_year": row.fiscal_year,
                "category": row.category,
                "value": getattr(row, value_key) or Decimal(0),
                "source_url": row.source_url,
            }
            for row in rows
        ]
