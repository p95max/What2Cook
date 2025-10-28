"""
Normalization and fuzzy helpers for ingredient matching.
"""
import unicodedata
from typing import List
from rapidfuzz import process, fuzz

def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if ord(c) < 128)
    return s

def normalize_list(items: List[str]) -> List[str]:
    return [normalize_text(i) for i in items if i and i.strip()]

def fuzzy_best_match(name: str, choices: list[str], score_cutoff: int = 80):
    if not choices:
        return None, 0
    match, score, _ = process.extractOne(name, choices, scorer=fuzz.QRatio) or (None, 0, None)
    return match, score
