"""
Utilities for mapping free-text user ingredient inputs to canonical
Ingredient names from the DB.

Behavior:
- Normalize user inputs (strip, lowercase, remove extra chars).
- Try exact case-insensitive match.
- If no exact match, try ILIKE '%token%' fuzzy search (first token, then full string).
- Return a list of unique matching ingredient names (canonical DB names),
  preserving rough order of user inputs (most relevant first).
"""

import re
from typing import List, Iterable, Set
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Ingredient


_normalize_re = re.compile(r"[^a-zA-Z0-9\u00C0-\u024F\s-]")


def _normalize(s: str) -> str:
    s2 = s.strip().lower()
    s2 = _normalize_re.sub("", s2)
    s2 = re.sub(r"\s+", " ", s2)
    return s2


async def map_input_to_ingredient_names(session: AsyncSession, user_inputs: Iterable[str], max_per_input: int = 5) -> List[str]:
    """
    Map a list/iterable of user-provided ingredient strings to canonical Ingredient.name values
    from the database.

    Returns a list of unique ingredient names (strings). If nothing found for an input,
    that input is skipped.
    """
    if not user_inputs:
        return []

    out: List[str] = []
    seen: Set[str] = set()

    inputs = [i for i in (s or "" for s in user_inputs) if i.strip()]
    normalized_inputs = [_normalize(i) for i in inputs if i.strip()]

    for raw, norm in zip(inputs, normalized_inputs):
        if not norm:
            continue

        stmt = select(Ingredient.name).where(func.lower(Ingredient.name) == norm)
        res = await session.execute(stmt)
        rows = [r[0] for r in res.fetchall()]
        for name in rows[:max_per_input]:
            if name not in seen:
                out.append(name)
                seen.add(name)
        if rows:
            continue

        ilike_stmt = select(Ingredient.name).where(Ingredient.name.ilike(f"%{norm}%")).limit(max_per_input)
        res = await session.execute(ilike_stmt)
        rows = [r[0] for r in res.fetchall()]
        for name in rows:
            if name not in seen:
                out.append(name)
                seen.add(name)
        if rows:
            continue

        tokens = [t for t in re.split(r"\s+", norm) if len(t) > 2]
        tokens = sorted(tokens, key=lambda x: -len(x))
        for tok in tokens:
            tok_stmt = select(Ingredient.name).where(Ingredient.name.ilike(f"%{tok}%")).limit(max_per_input)
            res = await session.execute(tok_stmt)
            rows = [r[0] for r in res.fetchall()]
            for name in rows:
                if name not in seen:
                    out.append(name)
                    seen.add(name)
            if rows:
                break

    return out
