"""
Pydantic schemas for API I/O.
"""
from typing import List, Optional
from pydantic import BaseModel

class IngredientOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class RecipeSearchOut(BaseModel):
    id: int
    title: str
    score: float
    match_count: int
    missing: List[str]
    have: List[str]
    ingredients: List[str]

    class Config:
        orm_mode = True

class IngredientsQuery(BaseModel):
    ingredients: List[str]
    limit: Optional[int] = 20
    page: Optional[int] = 1
    min_score: Optional[float] = 0.0
