"""
Scoring recipes by user ingredients.
"""
from typing import List, Dict

def score_recipe(recipe_ingredients: List[str], user_ingredients: List[str]) -> Dict:
    recipe_set = set(recipe_ingredients)
    user_set = set(user_ingredients)
    match = recipe_set & user_set
    missing = list(recipe_set - user_set)
    score = len(match) / max(len(recipe_set), 1)
    return {"score": score, "match_count": len(match), "missing": missing}
