import asyncio
from sqlalchemy import text
from db import engine

async def main():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT current_database(), current_user")
            )
            print("Database connection successful:", result.fetchone())
    except Exception as e:
        print("Database connection failed:", e)
    finally:
        await engine.dispose()

asyncio.run(main())