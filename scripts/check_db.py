"""Quick check that DATABASE_URL in .env can reach Postgres.

Run from the project root: python scripts/check_db.py
"""
import asyncio
import sys
from pathlib import Path

# Level 1 fix: moved out of the root (pytest would treat test.py as a test),
# so add the project root to the import path to find db.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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