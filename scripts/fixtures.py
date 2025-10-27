"""
Common fixtures loader: insert 10 simple, everyday recipes and ingredients.
"""
import asyncio
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal, init_db
from app.models import Ingredient, Recipe, recipe_ingredient

FIXTURES = [
    {
        "title": "Scrambled Eggs",
        "instructions": "Beat eggs with a pinch of salt and pepper. Melt butter in a pan and cook eggs over medium heat, stirring until softly set.",
        "prep_minutes": 8,
        "servings": 1,
        "source": "fixtures_common",
        "ingredients": [
            ("egg", 3, "pcs"),
            ("butter", 10, "g"),
            ("salt", None, "to taste"),
            ("black pepper", None, "to taste"),
            ("milk", 20, "ml"),
        ],
    },
    {
        "title": "Boiled Potatoes with Butter",
        "instructions": "Boil washed potatoes in salted water until tender. Drain and toss with butter and a pinch of salt. Serve hot.",
        "prep_minutes": 25,
        "servings": 2,
        "source": "fixtures_common",
        "ingredients": [
            ("potato", 600, "g"),
            ("salt", None, "to taste"),
            ("butter", 20, "g"),
            ("fresh parsley", None, "to taste"),
        ],
    },
    {
        "title": "Tomato Pasta",
        "instructions": "Cook pasta according to package. Sauté chopped onion and garlic in oil, add chopped tomatoes, simmer and season. Toss with pasta.",
        "prep_minutes": 20,
        "servings": 2,
        "source": "fixtures_common",
        "ingredients": [
            ("pasta", 200, "g"),
            ("tomato", 3, "pcs"),
            ("onion", 1, "pcs"),
            ("garlic", 1, "clove"),
            ("vegetable oil", 1, "tbsp"),
            ("salt", None, "to taste"),
            ("black pepper", None, "to taste"),
        ],
    },
    {
        "title": "Rice with Mixed Vegetables",
        "instructions": "Cook rice. Sauté diced carrot, peas and onion in oil, add cooked rice and soy sauce, stir until heated.",
        "prep_minutes": 25,
        "servings": 2,
        "source": "fixtures_common",
        "ingredients": [
            ("rice", 200, "g"),
            ("carrot", 1, "pcs"),
            ("frozen peas", 100, "g"),
            ("onion", 1, "pcs"),
            ("vegetable oil", 1, "tbsp"),
            ("soy sauce", 1, "tbsp"),
            ("salt", None, "to taste"),
        ],
    },
    {
        "title": "Simple Chicken Soup",
        "instructions": "Simmer chicken pieces with onion, carrot and celery in water until tender. Season with salt and serve with bread.",
        "prep_minutes": 60,
        "servings": 4,
        "source": "fixtures_common",
        "ingredients": [
            ("chicken pieces", 600, "g"),
            ("onion", 1, "pcs"),
            ("carrot", 2, "pcs"),
            ("celery", 1, "stalk"),
            ("water", 1500, "ml"),
            ("salt", None, "to taste"),
            ("black pepper", None, "to taste"),
        ],
    },
    {
        "title": "Fresh Vegetable Salad",
        "instructions": "Chop tomato, cucumber and onion. Toss with olive oil, lemon juice, salt and pepper. Serve fresh.",
        "prep_minutes": 10,
        "servings": 2,
        "source": "fixtures_common",
        "ingredients": [
            ("tomato", 2, "pcs"),
            ("cucumber", 1, "pcs"),
            ("onion", 0.5, "pcs"),
            ("olive oil", 1, "tbsp"),
            ("lemon", 0.5, "pcs"),
            ("salt", None, "to taste"),
            ("black pepper", None, "to taste"),
        ],
    },
    {
        "title": "Grilled Cheese Sandwich",
        "instructions": "Butter two slices of bread, place cheese between them and fry in a pan until golden and the cheese melts.",
        "prep_minutes": 10,
        "servings": 1,
        "source": "fixtures_common",
        "ingredients": [
            ("bread", 2, "slices"),
            ("cheese", 2, "slices"),
            ("butter", 10, "g"),
        ],
    },
    {
        "title": "Oatmeal Porridge",
        "instructions": "Cook rolled oats with milk or water until soft. Add a spoon of sugar or honey and a sliced banana or apple to serve.",
        "prep_minutes": 10,
        "servings": 1,
        "source": "fixtures_common",
        "ingredients": [
            ("rolled oats", 60, "g"),
            ("milk", 200, "ml"),
            ("sugar", 1, "tbsp"),
            ("banana", 1, "pcs"),
            ("salt", None, "pinch"),
        ],
    },
    {
        "title": "Banana Pancakes",
        "instructions": "Mash banana, mix with an egg and a little flour to make batter. Fry small pancakes until golden on both sides.",
        "prep_minutes": 15,
        "servings": 2,
        "source": "fixtures_common",
        "ingredients": [
            ("banana", 1, "pcs"),
            ("egg", 1, "pcs"),
            ("flour", 50, "g"),
            ("vegetable oil", 1, "tbsp"),
            ("salt", None, "pinch"),
        ],
    },
    {
        "title": "Potato Salad",
        "instructions": "Boil potatoes, cool and chop. Mix with chopped onion, boiled egg, a spoon of mayo, salt and pepper. Chill before serving.",
        "prep_minutes": 30,
        "servings": 3,
        "source": "fixtures_common",
        "ingredients": [
            ("potato", 500, "g"),
            ("egg", 2, "pcs"),
            ("onion", 0.5, "pcs"),
            ("mayonnaise", 2, "tbsp"),
            ("salt", None, "to taste"),
            ("black pepper", None, "to taste"),
        ],
    },
]


async def load_fixtures() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        for item in FIXTURES:
            ing_objs = []
            for name, qty, unit in item["ingredients"]:
                q = await session.execute(select(Ingredient).where(Ingredient.name == name))
                ing = q.scalars().first()
                if not ing:
                    ing = Ingredient(name=name)
                    session.add(ing)
                    await session.flush()
                ing_objs.append((ing, qty, unit))
            recipe = Recipe(
                title=item["title"],
                instructions=item["instructions"],
                prep_minutes=item.get("prep_minutes"),
                servings=item.get("servings"),
                source=item.get("source"),
            )
            session.add(recipe)
            await session.flush()
            for ing, qty, unit in ing_objs:
                await session.execute(
                    insert(recipe_ingredient).values(
                        recipe_id=recipe.id, ingredient_id=ing.id, quantity=qty, unit=unit
                    )
                )
        await session.commit()
    print("Loaded fixtures:", len(FIXTURES))


if __name__ == "__main__":
    asyncio.run(load_fixtures())
