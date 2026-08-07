import asyncio

from sqlalchemy import text

from app.database.models import Base
from app.database.session import get_engine


async def init_database() -> None:
    engine = get_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_spending_agency_year_category "
                "ON spending_records (agency_code, fiscal_year, category)"
            )
        )
    await engine.dispose()
    print("FedLens database schema initialized.")


if __name__ == "__main__":
    asyncio.run(init_database())
