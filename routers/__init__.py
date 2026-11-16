# Level 2: routers are the thin HTTP layer. Each route reads the request,
# calls one service method and returns the result. No SQL, no business rules.
from routers import documents, extraction, health

__all__ = ["documents", "extraction", "health"]
