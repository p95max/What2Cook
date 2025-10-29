from typing import Optional
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    aliases = Column(JSON, nullable=True, default=list)

    recipes = relationship("Recipe", secondary="recipe_ingredient", back_populates="ingredients")

    def __repr__(self) -> str:
        return f"<Ingredient id={self.id} name={self.name!r}>"
