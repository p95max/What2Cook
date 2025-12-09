"""initial

Revision ID: ca3137948eb4
Revises:
Create Date: 2025-10-29 10:01:25.213808
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ca3137948eb4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ingredients
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingredients_name"), "ingredients", ["name"], unique=True)

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("prep_minutes", sa.Integer(), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(length=1024), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("image_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recipes_title"), "recipes", ["title"], unique=False)
    op.alter_column("recipes", "likes_count", server_default=None)

    # m2m
    op.create_table(
        "recipe_ingredient",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("recipe_id", "ingredient_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("recipe_ingredient")
    op.drop_index(op.f("ix_recipes_title"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_index(op.f("ix_ingredients_name"), table_name="ingredients")
    op.drop_table("ingredients")
