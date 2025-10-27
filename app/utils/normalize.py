"""
Ingredient normalization utilities.
"""
import unicodedata
from typing import List

def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if ord(c) < 128)
    return s

def normalize_ingredients_list(items: List[str]) -> List[str]:
    return [normalize_text(i) for i in items if i and i.strip()]
