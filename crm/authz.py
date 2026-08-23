"""Shared row-level authorization helpers for staff-facing CRM endpoints."""
from __future__ import annotations

from fastapi import HTTPException

from schema import MODULES

# These modules intentionally represent organization-wide reference knowledge.
# Agents may read them even when another employee is listed as the owner.
SHARED_MODULES = frozenset({"competitors", "competitor_products", "market_research", "products"})


def _row_value(row, key, default=None):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _same_id(left, right) -> bool:
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return False


def can_access_record(user: dict, row, module: str) -> bool:
    """Whether a staff user may access one CRM row.

    Admins, managers and read-only users retain their normal broad read access.
    A sales agent is limited to their own records (or unassigned records), except
    for organization-wide reference modules defined above.
    """
    if user.get("role") != "agent" or module in SHARED_MODULES:
        return True
    owner_id = _row_value(row, "owner_id")
    return owner_id in (None, "") or _same_id(owner_id, user.get("id"))


def scope_clause(user: dict, module: str, owner_column: str = "owner_id") -> tuple[str, list]:
    """SQL clause and parameters that apply the same row-level policy to lists."""
    if user.get("role") == "agent" and module not in SHARED_MODULES:
        return f"({owner_column}=? OR {owner_column} IS NULL)", [user["id"]]
    return "1=1", []


def record_or_404(con, module: str, rid: int, user: dict, *, deleted_column: bool = True):
    """Load a module row and enforce row-level visibility without leaking its existence."""
    if module not in MODULES:
        raise HTTPException(404, "Unknown module")
    where = "id=?" + (" AND deleted=0" if deleted_column else "")
    row = con.execute(f'SELECT * FROM "{module}" WHERE {where}', (rid,)).fetchone()
    if not row or not can_access_record(user, row, module):
        raise HTTPException(404, "Not found")
    return row


def require_management(user: dict):
    if user.get("role") not in {"admin", "manager"}:
        raise HTTPException(403, "Manager permissions required")
