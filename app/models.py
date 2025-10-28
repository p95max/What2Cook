"""
SQLAlchemy models for recipe application.
"""
from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db import Base

recipe_ingredient = Table(
    "recipe_ingredient",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("ingredient_id", ForeignKey("ingredients.id"), primary_key=True),
    Column("quantity", Float, nullable=True),
    Column("unit", String, nullable=True),
)

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    aliases = Column(JSON, nullable=True)
    canonical = Column(Boolean, default=True)

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    instructions = Column(Text)
    prep_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    source = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    image_meta = Column(JSON, nullable=True)
    ingredients = relationship("Ingredient", secondary=recipe_ingredient, backref="recipes")
