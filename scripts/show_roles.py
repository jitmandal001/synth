"""Print every role and its permissions.

Run from the project root: python scripts/show_roles.py
"""
import asyncio
import sys
from pathlib import Path

# Level 3: find the project root so `core` can be imported from scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from core.database import engine


async def main() -> None:
    async with engine.connect() as conn:
        rows = await conn.execute(text(
            "SELECT r.name, p.name FROM roles r "
            "LEFT JOIN role_permissions rp ON rp.role_id = r.id "
            "LEFT JOIN permissions p ON p.id = rp.permission_id "
            "ORDER BY r.name, p.name"
        ))
        grants: dict[str, list[str]] = {}
        for role, perm in rows:
            grants.setdefault(role, []).append(perm)

        if not grants:
            print("No roles found.")
        for role, perms in grants.items():
            print(f"{role:<12} {', '.join(p for p in perms if p)}")
    await engine.dispose()


asyncio.run(main())