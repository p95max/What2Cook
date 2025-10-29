from typing import List, Optional
from pydantic import BaseModel


class IngredientOut(BaseModel):
    name: str

    class Config:
        orm_mode = True


class RecipeOut(BaseModel):
    id: int
    title: str
    instructions: Optional[str] = None
    prep_minutes: Optional[int] = None
    servings: Optional[int] = None
    source: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    image_meta: Optional[str] = None
    ingredients: List[str] = []

    class Config:
        orm_mode = True


class RecipeSearchOut(RecipeOut):
    score: float
    match_count: int
    missing: List[str] = []
    have: List[str] = []
