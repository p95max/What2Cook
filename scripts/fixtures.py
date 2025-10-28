"""
Fixtures loader with external image URLs: insert 10 common recipes and set image_url/thumbnail_url fields.
"""
import asyncio
from sqlalchemy import select, insert
from app.db import AsyncSessionLocal, init_db
from app.models import Ingredient, Recipe, recipe_ingredient

FIXTURES = [
    {
        "title": "Scrambled Eggs",
        "instructions": "Beat eggs with salt and pepper. Cook in butter until softly set.",
        "prep_minutes": 8,
        "servings": 1,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/20/Scrambed_eggs.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Scrambed_eggs.jpg/512px-Scrambed_eggs.jpg",
        "image_meta": {
            "author": "Takeaway",
            "page_url": "https://commons.wikimedia.org/wiki/File:Scrambed_eggs.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/2/20/Scrambed_eggs.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [
            ("egg", 3, "pcs"),
            ("butter", 10, "g"),
            ("salt", None, "to taste")
        ],
        "source": "wikimedia_commons"
    }
    ,
    {
        "title": "Boiled Potatoes with Butter",
        "instructions": "Boil potatoes until tender. Toss with butter and parsley.",
        "prep_minutes": 25,
        "servings": 2,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Hamburgers_with_Worcestershire_sauce%2C_on_boiled_yellow_potatoes_with_salt%2C_on_lettuce_with_garlic_olive_oil_-_Massachusetts.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Hamburgers_with_Worcestershire_sauce%2C_on_boiled_yellow_potatoes_with_salt%2C_on_lettuce_with_garlic_olive_oil_-_Massachusetts.jpg",
        "image_meta": {
            "author": "Daderot",
            "page_url": "https://commons.wikimedia.org/wiki/File:Hamburgers_with_Worcestershire_sauce,_on_boiled_yellow_potatoes_with_salt,_on_lettuce_with_garlic_olive_oil_-_Massachusetts.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Hamburgers_with_Worcestershire_sauce%2C_on_boiled_yellow_potatoes_with_salt%2C_on_lettuce_with_garlic_olive_oil_-_Massachusetts.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("potato", 600, "g"), ("butter", 20, "g"), ("salt", None, "to taste")],
    },
    {
        "title": "Tomato Pasta",
        "instructions": "Cook pasta and toss with a simple tomato, garlic and onion sauce.",
        "prep_minutes": 20,
        "servings": 2,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/71/Pasta_al_pomodoro.JPG",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/7/71/Pasta_al_pomodoro.JPG",
        "image_meta": {
            "author": "Roberto De Martino",
            "page_url": "https://commons.wikimedia.org/wiki/File:Pasta_al_pomodoro.JPG",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/7/71/Pasta_al_pomodoro.JPG",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("pasta", 200, "g"), ("tomato", 3, "pcs"), ("onion", 1, "pcs"), ("garlic", 1, "clove")],
    },
    {
        "title": "Rice with Vegetables",
        "instructions": "Cook rice and stir-fry mixed vegetables, then combine with soy sauce.",
        "prep_minutes": 25,
        "servings": 2,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Chicken_jambalaya_-_2010.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Chicken_jambalaya_-_2010.jpg",
        "image_meta": {
            "author": "Craig Murphy",
            "page_url": "https://commons.wikimedia.org/wiki/File:Chicken_jambalaya_-_2010.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Chicken_jambalaya_-_2010.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("rice", 200, "g"), ("carrot", 1, "pcs"), ("frozen peas", 100, "g"), ("onion", 1, "pcs")],
    },
    {
        "title": "Simple Chicken Soup",
        "instructions": "Simmer chicken with onion, carrot and celery for a light soup.",
        "prep_minutes": 60,
        "servings": 4,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Simple_vegetable_soup_2009.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Simple_vegetable_soup_2009.jpg",
        "image_meta": {
            "author": "Scott Teresi",
            "page_url": "https://commons.wikimedia.org/wiki/File:Simple_vegetable_soup_2009.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Simple_vegetable_soup_2009.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("chicken pieces", 600, "g"), ("onion", 1, "pcs"), ("carrot", 2, "pcs")],
    },
    {
        "title": "Fresh Vegetable Salad",
        "instructions": "Chop fresh vegetables and dress with olive oil and lemon.",
        "prep_minutes": 10,
        "servings": 2,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Fresh_salads.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Fresh_salads.jpg",
        "image_meta": {
            "author": "Ester Gasper Kimario",
            "page_url": "https://commons.wikimedia.org/wiki/File:Fresh_salads.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Fresh_salads.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("tomato", 2, "pcs"), ("cucumber", 1, "pcs"), ("onion", 0.5, "pcs"), ("olive oil", 1, "tbsp")],
    },
    {
        "title": "Grilled Cheese Sandwich",
        "instructions": "Butter bread, add cheese and fry until golden and melted.",
        "prep_minutes": 10,
        "servings": 1,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Grilled_Cheese_Sandwich.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Grilled_Cheese_Sandwich.jpg",
        "image_meta": {
            "author": "Quickspicerecipes",
            "page_url": "https://commons.wikimedia.org/wiki/File:Grilled_Cheese_Sandwich.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Grilled_Cheese_Sandwich.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("bread", 2, "slices"), ("cheese", 2, "slices"), ("butter", 10, "g")],
    },
    {
        "title": "Oatmeal Porridge",
        "instructions": "Cook oats with milk or water and top with banana or honey.",
        "prep_minutes": 10,
        "servings": 1,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Oatmeal_porridge_with_fruits_5.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Oatmeal_porridge_with_fruits_5.jpg",
        "image_meta": {
            "author": "Shisma",
            "page_url": "https://commons.wikimedia.org/wiki/File:Oatmeal_porridge_with_fruits_4.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/b/bf/Oatmeal_porridge_with_fruits_4.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("rolled oats", 60, "g"), ("milk", 200, "ml"), ("banana", 1, "pcs")],
    },
    {
        "title": "Banana Pancakes",
        "instructions": "Mash banana, mix with egg and a little flour, fry small pancakes.",
        "prep_minutes": 15,
        "servings": 2,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/81/Healthy_Banana_Pancakes.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/8/81/Healthy_Banana_Pancakes.jpg",
        "image_meta": {
            "author": "FitTasteTic",
            "page_url": "https://commons.wikimedia.org/wiki/File:Healthy_Banana_Pancakes.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/8/81/Healthy_Banana_Pancakes.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("banana", 1, "pcs"), ("egg", 1, "pcs"), ("flour", 50, "g")],
    },
    {
        "title": "Potato Salad",
        "instructions": "Mix boiled potatoes with chopped egg, mayo and onion. Chill before serving.",
        "prep_minutes": 30,
        "servings": 3,

        "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Warm_kipfler_potato_salad.jpg",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Warm_kipfler_potato_salad.jpg",
        "image_meta": {
            "author": "jules",
            "page_url": "https://commons.wikimedia.org/wiki/File:Warm_kipfler_potato_salad.jpg",
            "file_url": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Warm_kipfler_potato_salad.jpg",
            "license": "CC BY-SA 3.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/3.0"
        },

        "ingredients": [("potato", 500, "g"), ("egg", 2, "pcs"), ("mayonnaise", 2, "tbsp")],
    },
]

async def load_fixtures() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
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
                image_url=item.get("image_url"),
                thumbnail_url=item.get("thumbnail_url"),
                source="fixtures_with_external_images",
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
    print("Loaded fixtures with external images:", len(FIXTURES))

if __name__ == "__main__":
    asyncio.run(load_fixtures())
