from typing import List, Optional
from pydantic import BaseModel, Field, conint, confloat


class IngredientsQuery(BaseModel):
    ingredients: List[str] = Field(..., min_items=1, max_items=50, description="List of ingredient names (user input)")
    page: Optional[conint(ge=1)] = Field(1, description="Page number")
    limit: Optional[conint(ge=1, le=100)] = Field(20, description="Items per page")
    min_score: Optional[confloat(ge=0.0, le=1.0)] = Field(0.0, description="Minimum match score to include")
