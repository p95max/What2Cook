from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

recipe_ingredient = Table(
    "recipe_ingredient",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True),
)


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    instructions = Column(Text, nullable=True)
    prep_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    source = Column(String(255), nullable=True)
    image_url = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)
    image_meta = Column(String(1024), nullable=True)

    likes_count = Column(Integer, default=0, nullable=False)

    ingredients = relationship("Ingredient", secondary=recipe_ingredient, back_populates="recipes")

    def __repr__(self) -> str:
        return f"<Recipe id={self.id} title={self.title!r}>"
