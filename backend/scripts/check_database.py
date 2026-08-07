import asyncio

from sqlalchemy import text

from app.database.session import session_scope


async def check_database() -> None:
    try:
        async with session_scope() as session:
            result = await session.scalar(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to Neon. Check DATABASE_URL, network access, and SSL settings."
        ) from exc
    if result != 1:
        raise RuntimeError("Database health check returned an unexpected result")
    print("Neon database connection succeeded.")


if __name__ == "__main__":
    asyncio.run(check_database())
