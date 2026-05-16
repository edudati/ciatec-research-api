from sqlalchemy import text

from src.core.database import engine


async def ping_database() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
